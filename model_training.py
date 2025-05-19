import pandas as pd
import numpy as np
import pickle
import json
import hashlib
import time
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler
from sklearn.ensemble import RandomForestClassifier, RandomForestRegressor
from sklearn.linear_model import LogisticRegression, LinearRegression
from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score, r2_score, mean_squared_error


class ModelTrainer:
    """
    Service for training machine learning models on datasets from the marketplace.
    """

    def __init__(self, ipfs_service):
        """
        Initialize the model trainer with the IPFS service.

        Args:
            ipfs_service: The IPFS service for retrieving and storing data
        """
        self.ipfs_service = ipfs_service

    def train_model(self, dataset_content, algorithm_type, target_column, algorithm_params=None, test_size=0.2,
                    random_state=42):
        """
        Train a machine learning model on the provided dataset.

        Args:
            dataset_content (bytes): Raw dataset content
            algorithm_type (str): Type of algorithm to use ('classification' or 'regression')
            target_column (str): Name of the target column
            algorithm_params (dict, optional): Parameters for the algorithm
            test_size (float, optional): Proportion of data to use for testing
            random_state (int, optional): Random seed for reproducibility

        Returns:
            dict: Results including metrics, model CID, and training information
        """
        # Default parameters if none provided
        if algorithm_params is None:
            algorithm_params = {}

        # Parse dataset (assuming CSV)
        try:
            # Convert bytes to string and parse CSV
            csv_content = dataset_content.decode('utf-8')
            df = pd.read_csv(pd.io.common.StringIO(csv_content))
        except Exception as e:
            return {"error": f"Failed to parse dataset: {str(e)}"}

        # Basic preprocessing
        # Handle missing values
        df = df.dropna()

        # Separate features and target
        if target_column not in df.columns:
            return {"error": f"Target column '{target_column}' not found in dataset"}

        X = df.drop(target_column, axis=1)
        y = df[target_column]

        # Handle non-numeric columns
        X = pd.get_dummies(X)

        # Split data
        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=test_size, random_state=random_state
        )

        # Standardize features
        scaler = StandardScaler()
        X_train_scaled = scaler.fit_transform(X_train)
        X_test_scaled = scaler.transform(X_test)

        # Train model based on algorithm type
        start_time = time.time()

        if algorithm_type == 'classification':
            # Determine if binary or multiclass
            if len(np.unique(y)) == 2:
                algorithm = algorithm_params.get('algorithm', 'logistic')
                if algorithm == 'logistic':
                    model = LogisticRegression(random_state=random_state)
                else:  # default to random forest
                    model = RandomForestClassifier(random_state=random_state)

                model.fit(X_train_scaled, y_train)
                y_pred = model.predict(X_test_scaled)

                # Calculate metrics
                metrics = {
                    'accuracy': float(accuracy_score(y_test, y_pred)),
                    'precision': float(precision_score(y_test, y_pred, average='binary')),
                    'recall': float(recall_score(y_test, y_pred, average='binary')),
                    'f1_score': float(f1_score(y_test, y_pred, average='binary'))
                }
            else:
                # Multiclass classification
                model = RandomForestClassifier(random_state=random_state)
                model.fit(X_train_scaled, y_train)
                y_pred = model.predict(X_test_scaled)

                # Calculate metrics
                metrics = {
                    'accuracy': float(accuracy_score(y_test, y_pred)),
                    'f1_score': float(f1_score(y_test, y_pred, average='weighted'))
                }

        elif algorithm_type == 'regression':
            algorithm = algorithm_params.get('algorithm', 'linear')
            if algorithm == 'linear':
                model = LinearRegression()
            else:  # default to random forest
                model = RandomForestRegressor(random_state=random_state)

            model.fit(X_train_scaled, y_train)
            y_pred = model.predict(X_test_scaled)

            # Calculate metrics
            metrics = {
                'r2_score': float(r2_score(y_test, y_pred)),
                'mse': float(mean_squared_error(y_test, y_pred)),
                'rmse': float(np.sqrt(mean_squared_error(y_test, y_pred)))
            }
        else:
            return {"error": f"Unsupported algorithm type: {algorithm_type}"}

        training_time = time.time() - start_time

        # Save model to IPFS
        model_binary = pickle.dumps(model)

        # Create model metadata
        model_metadata = {
            'algorithm_type': algorithm_type,
            'feature_columns': list(X.columns),
            'target_column': target_column,
            'metrics': metrics,
            'training_time': training_time,
            'samples_count': len(df),
            'training_date': time.strftime('%Y-%m-%d %H:%M:%S'),
            'scaler': pickle.dumps(scaler).hex()  # Save scaler for future predictions
        }

        # Save to IPFS
        model_cid = self.ipfs_service.add(model_binary, model_metadata)
        self.ipfs_service.pin(model_cid)

        # Return results
        result = {
            'model_cid': model_cid,
            'metrics': metrics,
            'training_time': training_time,
            'features_count': len(X.columns),
            'samples_count': len(df)
        }

        return result

    def get_model(self, model_cid):
        """
        Retrieve a model from IPFS.

        Args:
            model_cid: IPFS CID of the model

        Returns:
            tuple: (model, metadata)
        """
        model_binary = self.ipfs_service.get(model_cid)
        if not model_binary:
            return None, None

        model = pickle.loads(model_binary)
        metadata = self.ipfs_service.get_metadata(model_cid)

        return model, metadata

    def predict(self, model_cid, data):
        """
        Make predictions using a stored model.

        Args:
            model_cid: IPFS CID of the model
            data: DataFrame or JSON data for prediction

        Returns:
            Predictions
        """
        model, metadata = self.get_model(model_cid)
        if model is None:
            return {"error": "Model not found"}

        # Parse input data
        if isinstance(data, str):
            try:
                data = json.loads(data)
            except:
                return {"error": "Invalid JSON input"}

        if isinstance(data, dict):
            # Convert single record to DataFrame
            data = pd.DataFrame([data])

        # Ensure all expected features are present
        feature_columns = metadata.get('feature_columns', [])
        missing_columns = [col for col in feature_columns if col not in data.columns]
        if missing_columns:
            return {"error": f"Missing columns in input data: {missing_columns}"}

        # Apply preprocessing (one-hot encoding)
        data = pd.get_dummies(data)

        # Match columns with training data
        for col in feature_columns:
            if col not in data.columns:
                data[col] = 0

        # Use only the expected columns in the right order
        data = data[feature_columns]

        # Apply scaling if available
        if 'scaler' in metadata:
            scaler = pickle.loads(bytes.fromhex(metadata['scaler']))
            data_scaled = scaler.transform(data)
        else:
            data_scaled = data

        # Make prediction
        predictions = model.predict(data_scaled)

        return {"predictions": predictions.tolist()}