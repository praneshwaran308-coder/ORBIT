import re

import pandas as pd

from sklearn.linear_model import (
    LinearRegression,
    LogisticRegression
)

from sklearn.metrics import (
    mean_absolute_error,
    r2_score,
    accuracy_score,
    precision_score,
    recall_score,
    f1_score
)

from sklearn.model_selection import train_test_split

from sklearn.tree import (
    DecisionTreeRegressor,
    DecisionTreeClassifier
)

from sklearn.ensemble import (
    RandomForestRegressor,
    RandomForestClassifier
)

from .base_agent import BaseAgent


class MLAgent(BaseAgent):

    def __init__(self):
        super().__init__("ML Agent")


    # =========================================================
    # TARGET DETECTION
    # =========================================================

    def detect_target(
        self,
        task: str,
        columns: list
    ) -> str | None:

        task_lower = task.lower()

        target_patterns = [
            r"(?:predict|forecast|estimate|classify|classifying)"
            r"\s+(?:the\s+)?([a-zA-Z_][a-zA-Z0-9_]*)",

            r"(?:predict|classify|classifying)"
            r"\s+.*?\b([a-zA-Z_][a-zA-Z0-9_]*)"
            r"\s+(?:groups|group|categories|category|classes|class)"
        ]

        # An explicit target named immediately after the modeling
        # action takes precedence over any feature names in the task.
        for pattern in target_patterns:

            match = re.search(
                pattern,
                task_lower
            )

            if match:

                requested_target = match.group(1)

                for column in columns:

                    if column.lower() == requested_target:
                        return column

        priority_columns = []

        target_words = [
            "salary",
            "price",
            "income",
            "revenue",
            "score",
            "profit",
            "age",
            "target"
        ]

        for word in target_words:

            if word in task_lower:

                for column in columns:

                    if column.lower() == word:
                        priority_columns.append(column)

        # Classification-specific wording.
        # Example:
        # "Classify employees into Low, Medium, and High
        # salary groups" -> salary is the target.

        classification_phrases = [
            "salary groups",
            "salary group",
            "salary categories",
            "salary category",
            "salary classes",
            "salary class",
            "salary levels",
            "salary bands"
        ]

        for phrase in classification_phrases:

            if phrase in task_lower:

                for column in columns:

                    if column.lower() == "salary":
                        return column

        # Explicit target-oriented column mention.
        for column in columns:

            column_lower = column.lower()

            if any(
                column_lower == item.lower()
                for item in priority_columns
            ):
                return column

        # Never blindly select the first numeric column.
        return None


    # =========================================================
    # TASK TYPE DETECTION
    # =========================================================

    def detect_task_type(
        self,
        task: str
    ) -> str:

        task_lower = task.lower()

        classification_keywords = [

            "classify",
            "classification",
            "classifier",
            "classifying",

            "category",
            "categories",
            "categorize",
            "categorise",

            "group",
            "groups",
            "grouping",

            "label",
            "labels",

            "low medium high",
            "low, medium, high",
            "low / medium / high",

            "yes or no",
            "binary classification",

            "fraud detection",
            "spam detection",

            "predict class",
            "predict category"
        ]

        if any(
            keyword in task_lower
            for keyword in classification_keywords
        ):

            return "classification"


        return "regression"


    # =========================================================
    # CLASS CREATION
    # =========================================================

    def create_classes(
        self,
        target_series: pd.Series
    ):

        """
        Convert a numeric target into three balanced
        categories:

        Low
        Medium
        High

        Quantile-based classification is used so the
        classes remain reasonably balanced for small
        datasets.
        """

        try:

            labels = [
                "Low",
                "Medium",
                "High"
            ]

            classes = pd.qcut(
                target_series,
                q=3,
                labels=labels,
                duplicates="drop"
            )

            # qcut can theoretically produce fewer than
            # three classes when many target values are
            # identical.

            unique_classes = (
                classes
                .dropna()
                .unique()
            )

            if len(unique_classes) < 2:

                return None

            return classes

        except Exception:

            return None


    # =========================================================
    # EXTRACT NEW INPUT
    # =========================================================

    def extract_prediction_input(
        self,
        task: str,
        features: list
    ) -> dict:

        """
        Extract values such as:

        age 27
        experience 4

        from a prediction request.

        This is intentionally simple and deterministic.
        """

        task_lower = task.lower()

        values = {}

        for feature in features:

            pattern = (
                rf"\b{re.escape(feature.lower())}"
                rf"\s*(?:is|=|:)?\s*"
                rf"(-?\d+(?:\.\d+)?)"
            )

            match = re.search(
                pattern,
                task_lower
            )

            if match:

                raw_value = match.group(1)

                try:

                    number = float(
                        raw_value
                    )

                    if number.is_integer():

                        number = int(
                            number
                        )

                    values[feature] = number

                except ValueError:

                    pass

        return values


    # =========================================================
    # REGRESSION
    # =========================================================

    async def run_regression(
        self,
        task: str,
        model_data: pd.DataFrame,
        features: list,
        target: str
    ) -> dict:

        X = model_data[features]

        y = model_data[target]


        # -----------------------------------------------------
        # Train/test split
        # -----------------------------------------------------

        X_train, X_test, y_train, y_test = (
            train_test_split(
                X,
                y,
                test_size=0.2,
                random_state=42
            )
        )


        # -----------------------------------------------------
        # Models
        # -----------------------------------------------------

        models = {

            "Linear Regression":
                LinearRegression(),

            "Decision Tree":
                DecisionTreeRegressor(
                    random_state=42,
                    max_depth=5
                ),

            "Random Forest":
                RandomForestRegressor(
                    n_estimators=100,
                    random_state=42,
                    max_depth=5
                )
        }


        model_results = {}


        # -----------------------------------------------------
        # Train + evaluate
        # -----------------------------------------------------

        for model_name, model in models.items():

            model.fit(
                X_train,
                y_train
            )

            predictions = model.predict(
                X_test
            )

            mae = mean_absolute_error(
                y_test,
                predictions
            )

            r2 = r2_score(
                y_test,
                predictions
            )

            model_results[
                model_name
            ] = {

                "mean_absolute_error":
                    float(mae),

                "r2_score":
                    float(r2)
            }


        # -----------------------------------------------------
        # Best model
        # -----------------------------------------------------

        best_model_name = max(
            model_results,
            key=lambda name:
                model_results[name]["r2_score"]
        )


        # -----------------------------------------------------
        # Train best model on full dataset
        # -----------------------------------------------------

        best_model = models[
            best_model_name
        ]

        best_model.fit(
            X,
            y
        )


        # -----------------------------------------------------
        # New prediction
        # -----------------------------------------------------

        prediction_input = (
            self.extract_prediction_input(
                task,
                features
            )
        )


        prediction = None


        if len(prediction_input) == len(
            features
        ):

            input_frame = pd.DataFrame(
                [
                    [
                        prediction_input[
                            feature
                        ]
                        for feature in features
                    ]
                ],
                columns=features
            )

            predicted_value = (
                best_model
                .predict(input_frame)[0]
            )

            prediction = {

                "input":
                    prediction_input,

                "predicted_value":
                    float(predicted_value)
            }


        result = {

            "agent": self.name,

            "task": task,

            "status": "completed",

            "task_type": "regression",

            "target": target,

            "features": features,

            "dataset_rows":
                len(model_data),

            "training_rows":
                len(X_train),

            "testing_rows":
                len(X_test),

            "best_model":
                best_model_name,

            "model_comparison":
                model_results
        }


        if prediction:

            result["prediction"] = prediction


        return result


    # =========================================================
    # CLASSIFICATION
    # =========================================================

    async def run_classification(
        self,
        task: str,
        model_data: pd.DataFrame,
        features: list,
        target: str
    ) -> dict:

        # -----------------------------------------------------
        # Create target classes
        # -----------------------------------------------------

        classes = self.create_classes(
            model_data[target]
        )


        if classes is None:

            return {

                "agent": self.name,

                "task": task,

                "status": "classification_error",

                "result": (
                    "Unable to create classification "
                    "categories from the target column."
                ),

                "target": target,

                "features": features
            }


        classification_data = (
            model_data
            .copy()
        )

        classification_data[
            "target_class"
        ] = classes


        classification_data = (
            classification_data
            .dropna()
        )


        X = classification_data[
            features
        ]

        y = classification_data[
            "target_class"
        ]


        # -----------------------------------------------------
        # Check class count
        # -----------------------------------------------------

        class_counts = (
            y.value_counts()
            .to_dict()
        )


        if len(class_counts) < 2:

            return {

                "agent": self.name,

                "task": task,

                "status": "classification_error",

                "result": (
                    "At least two target classes "
                    "are required for classification."
                ),

                "target": target,

                "features": features,

                "class_distribution":
                    {
                        str(key): int(value)
                        for key, value
                        in class_counts.items()
                    }
            }


        # -----------------------------------------------------
        # Train/test split
        #
        # Use stratification when every class has enough
        # samples.
        # -----------------------------------------------------

        stratify = y

        try:

            X_train, X_test, y_train, y_test = (
                train_test_split(
                    X,
                    y,
                    test_size=0.2,
                    random_state=42,
                    stratify=stratify
                )
            )

        except ValueError:

            # Fall back to normal split if the dataset
            # is too small for stratification.

            X_train, X_test, y_train, y_test = (
                train_test_split(
                    X,
                    y,
                    test_size=0.2,
                    random_state=42
                )
            )


        # -----------------------------------------------------
        # Classification models
        # -----------------------------------------------------

        models = {

            "Logistic Regression":
                LogisticRegression(
                    max_iter=1000,
                    random_state=42
                ),

            "Decision Tree Classifier":
                DecisionTreeClassifier(
                    random_state=42,
                    max_depth=5
                ),

            "Random Forest Classifier":
                RandomForestClassifier(
                    n_estimators=100,
                    random_state=42,
                    max_depth=5
                )
        }


        model_results = {}


        # -----------------------------------------------------
        # Train + evaluate
        # -----------------------------------------------------

        for model_name, model in models.items():

            try:

                model.fit(
                    X_train,
                    y_train
                )

                predictions = model.predict(
                    X_test
                )


                accuracy = accuracy_score(
                    y_test,
                    predictions
                )


                precision = precision_score(
                    y_test,
                    predictions,
                    average="weighted",
                    zero_division=0
                )


                recall = recall_score(
                    y_test,
                    predictions,
                    average="weighted",
                    zero_division=0
                )


                f1 = f1_score(
                    y_test,
                    predictions,
                    average="weighted",
                    zero_division=0
                )


                model_results[
                    model_name
                ] = {

                    "accuracy":
                        float(accuracy),

                    "precision":
                        float(precision),

                    "recall":
                        float(recall),

                    "f1_score":
                        float(f1)
                }


            except Exception as model_error:

                model_results[
                    model_name
                ] = {

                    "accuracy": 0.0,

                    "precision": 0.0,

                    "recall": 0.0,

                    "f1_score": 0.0,

                    "error":
                        str(model_error)
                }


        # -----------------------------------------------------
        # Make sure at least one model worked
        # -----------------------------------------------------

        if not model_results:

            return {

                "agent": self.name,

                "task": task,

                "status": "classification_error",

                "result": (
                    "None of the classification "
                    "models could be trained."
                )
            }


        # -----------------------------------------------------
        # Select best classifier by F1
        # -----------------------------------------------------

        best_model_name = max(
            model_results,
            key=lambda name:
                model_results[name]["f1_score"]
        )


        best_model = models[
            best_model_name
        ]


        # -----------------------------------------------------
        # Retrain best model on full data
        # -----------------------------------------------------

        best_model.fit(
            X,
            y
        )


        # -----------------------------------------------------
        # Optional classification input
        # -----------------------------------------------------

        prediction_input = (
            self.extract_prediction_input(
                task,
                features
            )
        )


        classification_prediction = None


        if len(prediction_input) == len(
            features
        ):

            input_frame = pd.DataFrame(
                [
                    [
                        prediction_input[
                            feature
                        ]
                        for feature in features
                    ]
                ],
                columns=features
            )


            predicted_class = (
                best_model
                .predict(input_frame)[0]
            )


            classification_prediction = {

                "input":
                    prediction_input,

                "predicted_class":
                    str(predicted_class)
            }


        # -----------------------------------------------------
        # Result
        # -----------------------------------------------------

        result = {

            "agent": self.name,

            "task": task,

            "status": "completed",

            "task_type": "classification",

            "target": target,

            "features": features,

            "dataset_rows":
                len(classification_data),

            "training_rows":
                len(X_train),

            "testing_rows":
                len(X_test),

            "classes": [
                str(value)
                for value in sorted(
                    y.unique()
                )
            ],

            "class_distribution": {

                str(key): int(value)

                for key, value
                in class_counts.items()
            },

            "best_model":
                best_model_name,

            "model_comparison":
                model_results
        }


        if classification_prediction:

            result[
                "classification_prediction"
            ] = classification_prediction


        return result


    # =========================================================
    # MAIN RUN
    # =========================================================

    async def run(
        self,
        task: str,
        file_path: str = None
    ) -> dict:

        """
        Train, compare and evaluate machine-learning
        regression or classification models.
        """

        # -----------------------------------------------------
        # File validation
        # -----------------------------------------------------

        if not file_path:

            return {

                "agent": self.name,

                "task": task,

                "status":
                    "waiting_for_file",

                "result": (
                    "Please provide a dataset "
                    "for ML analysis."
                )
            }


        try:

            # -------------------------------------------------
            # Read CSV
            # -------------------------------------------------

            df = pd.read_csv(
                file_path
            )


            # -------------------------------------------------
            # Validate dataset
            # -------------------------------------------------

            if df.empty:

                return {

                    "agent": self.name,

                    "task": task,

                    "status":
                        "invalid_dataset",

                    "result":
                        "The dataset is empty."
                }


            # -------------------------------------------------
            # Detect target
            # -------------------------------------------------

            target = self.detect_target(
                task,
                df.columns.tolist()
            )


            if not target:

                return {

                    "agent": self.name,

                    "task": task,

                    "status":
                        "target_required",

                    "result": (
                        "Could not determine the "
                        "target column. Please specify "
                        "what you want to predict or "
                        "classify."
                    ),

                    "available_columns":
                        df.columns.tolist()
                }


            # -------------------------------------------------
            # Validate target
            # -------------------------------------------------

            if not pd.api.types.is_numeric_dtype(
                df[target]
            ):

                return {

                    "agent": self.name,

                    "task": task,

                    "status":
                        "invalid_target",

                    "result": (
                        f"Target column '{target}' "
                        "must be numeric for the "
                        "current ML pipeline."
                    )
                }


            # -------------------------------------------------
            # Select numeric features
            # -------------------------------------------------

            numeric_columns = (
                df.select_dtypes(
                    include="number"
                )
                .columns
                .tolist()
            )


            features = [

                column

                for column
                in numeric_columns

                if column != target
            ]


            if not features:

                return {

                    "agent": self.name,

                    "task": task,

                    "status":
                        "no_features",

                    "result": (
                        "No numeric feature columns "
                        "were found other than the target."
                    )
                }


            # -------------------------------------------------
            # Remove missing values
            # -------------------------------------------------

            model_data = (
                df[
                    features + [target]
                ]
                .dropna()
            )


            # -------------------------------------------------
            # Detect ML task type
            # -------------------------------------------------

            task_type = self.detect_task_type(
                task
            )


            # -------------------------------------------------
            # Minimum dataset size
            # -------------------------------------------------

            minimum_rows = 10


            if len(model_data) < minimum_rows:

                return {

                    "agent": self.name,

                    "task": task,

                    "status":
                        "insufficient_data",

                    "result": (
                        f"The dataset contains only "
                        f"{len(model_data)} usable rows. "
                        f"At least {minimum_rows} rows "
                        "are required for a basic "
                        "train/test evaluation."
                    ),

                    "dataset_rows":
                        len(model_data),

                    "target":
                        target,

                    "features":
                        features,

                    "task_type":
                        task_type
                }


            # -------------------------------------------------
            # Classification
            # -------------------------------------------------

            if task_type == "classification":

                return await self.run_classification(
                    task,
                    model_data,
                    features,
                    target
                )


            # -------------------------------------------------
            # Regression
            # -------------------------------------------------

            return await self.run_regression(
                task,
                model_data,
                features,
                target
            )


        except Exception as error:

            return {

                "agent": self.name,

                "task": task,

                "status":
                    "error",

                "result":
                    str(error)
            }
