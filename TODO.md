x# TODO: Add Conversion for JSON and XLSX to CSV in Upload

## Overview
The upload currently allows JSON and XLSX files, but processing only works for CSV. We need to convert JSON and XLSX files to CSV format during upload so that the existing processing logic can handle them.

## Steps
- [ ] Modify `upload_view` in `analytics_app/views.py` to detect JSON/XLSX files and convert them to CSV before saving.
- [ ] Use pandas to read JSON (pd.read_json) or XLSX (pd.read_excel) and write to CSV (df.to_csv).
- [ ] Save the converted CSV content to the UploadedFile's file field.
- [ ] Update the file_type to 'csv' after conversion.
- [ ] Ensure the conversion handles errors gracefully and logs them.
- [ ] Test the conversion with sample JSON and XLSX files.
- [ ] Update processing task if needed (though it should work since file_type becomes 'csv').

## Dependencies
- Pandas is already installed (from requirements.txt).
- For XLSX, openpyxl is installed.

## Notes
- Conversion should be done in memory to avoid temporary files.
- Handle large files carefully to avoid memory issues.
