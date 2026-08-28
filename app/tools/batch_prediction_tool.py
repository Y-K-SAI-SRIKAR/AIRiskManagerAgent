import os
from pathlib import Path
from typing import Any

import httpx
from dotenv import load_dotenv


# Load environment variables from .env
load_dotenv()


class BatchPredictionTool:
    """
    Agent tool responsible for sending a CSV file to the
    production ML batch prediction service.

    The ML service handles:
        - preprocessing
        - batch inference
        - prediction generation
        - report generation
        - S3 uploads
        - presigned download URLs

    This tool only handles communication with the ML service.
    """

    name = "batch_prediction_tool"

    def __init__(self, ml_service_url: str | None = None):
        """
        Initialize the batch prediction tool.

        Args:
            ml_service_url:
                Optional ML service URL.
                If not provided, ML_SERVICE_URL is read from .env.
        """

        self.ml_service_url = (
            ml_service_url
            or os.getenv("ML_SERVICE_URL")
        )

        if not self.ml_service_url:
            raise ValueError(
                "ML_SERVICE_URL environment variable is not configured."
            )

        self.ml_service_url = self.ml_service_url.rstrip("/")

        self.endpoint = (
            f"{self.ml_service_url}/predict/batch"
        )

    async def analyze_csv(
        self,
        file_path: str | Path,
        filename: str | None = None,
    ) -> dict[str, Any]:
        """
        Send a CSV file to the ML batch prediction endpoint.

        Args:
            file_path:
                Local path of the CSV file.

            filename:
                Optional filename to send to the ML service.

        Returns:
            Standardized tool response.
        """

        path = Path(file_path)

        # --------------------------------------------------
        # Validate file existence
        # --------------------------------------------------

        if not path.exists():
            return {
                "success": False,
                "data": {},
                "error": f"File not found: {path}",
            }

        # --------------------------------------------------
        # Validate file type
        # --------------------------------------------------

        if not path.is_file():
            return {
                "success": False,
                "data": {},
                "error": f"Path is not a file: {path}",
            }

        if path.suffix.lower() != ".csv":
            return {
                "success": False,
                "data": {},
                "error": "Only CSV files are supported.",
            }

        upload_filename = filename or path.name

        # --------------------------------------------------
        # Call ML batch prediction service
        # --------------------------------------------------

        try:

            timeout = httpx.Timeout(
                connect=30.0,
                read=900.0,
                write=900.0,
                pool=30.0,
            )

            async with httpx.AsyncClient(
                timeout=timeout
            ) as client:

                with open(path, "rb") as file:

                    response = await client.post(
                        self.endpoint,
                        files={
                            "file": (
                                upload_filename,
                                file,
                                "text/csv",
                            )
                        },
                    )

            # --------------------------------------------------
            # Handle ML service HTTP errors
            # --------------------------------------------------

            if response.status_code != 200:

                try:
                    error_data = response.json()
                except Exception:
                    error_data = response.text

                return {
                    "success": False,
                    "data": {},
                    "error": (
                        "ML batch prediction failed "
                        f"(HTTP {response.status_code}): "
                        f"{error_data}"
                    ),
                }

            # --------------------------------------------------
            # Parse JSON response
            # --------------------------------------------------

            try:
                result = response.json()

            except Exception as exc:

                return {
                    "success": False,
                    "data": {},
                    "error": (
                        "ML batch prediction service returned "
                        f"invalid JSON: {exc}"
                    ),
                }

            # --------------------------------------------------
            # Successful response
            # --------------------------------------------------

            return {
                "success": True,
                "data": result,
                "error": None,
            }

        # --------------------------------------------------
        # Timeout
        # --------------------------------------------------

        except httpx.TimeoutException:

            return {
                "success": False,
                "data": {},
                "error": (
                    "ML batch prediction service timed out."
                ),
            }

        # --------------------------------------------------
        # Connection / network error
        # --------------------------------------------------

        except httpx.RequestError as exc:

            return {
                "success": False,
                "data": {},
                "error": (
                    "Unable to connect to ML batch "
                    f"prediction service: {exc}"
                ),
            }

        # --------------------------------------------------
        # Unexpected error
        # --------------------------------------------------

        except Exception as exc:

            return {
                "success": False,
                "data": {},
                "error": (
                    f"Unexpected batch prediction error: {exc}"
                ),
            }