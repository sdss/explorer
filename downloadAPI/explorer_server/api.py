from fastapi import FastAPI, HTTPException
from .models import DataFrameData, ExportResponse
from .config import get_settings
from .utils import generate_unique_filename, ensure_export_dir, create_vaex_dataframe
import os

app = FastAPI()
settings = get_settings()


@app.post("/export/csv", response_model=ExportResponse)
async def export_to_csv(data: DataFrameData):
    try:
        ensure_export_dir(settings.EXPORT_DIR)
        filename = generate_unique_filename()
        filepath = os.path.join(settings.EXPORT_DIR, filename)

        df = create_vaex_dataframe(data.columns)
        df.export_csv(filepath)

        file_url = f"/downloads/{filename}"

        return ExportResponse(
            status="success",
            filepath=filepath,
            download_url=file_url,
            row_count=len(df),
        )

    except Exception as e:
        raise HTTPException(status_code=500,
                            detail=f"Error processing DataFrame: {str(e)}")


@app.get("/health")
async def health_check():
    return {"status": "healthy"}
