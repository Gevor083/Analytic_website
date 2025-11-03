# TODO: Move Analyses Logic from JS to Python Backend

## 1. Edit views.py
- [ ] Add `get_numeric_fields(df)` function to identify numeric columns.
- [ ] Add `group_and_calculate_stats(df, x_field, y_field)` function to compute grouped statistics (mean, median, std, etc.).
- [ ] Modify `result_view` to compute processed chart data for all numeric field pairs and pass as `processed_chart_data` to template.

## 2. Edit result.html
- [ ] Update context to include `processed_chart_data`.
- [ ] Modify JS in template to use `processed_chart_data` instead of raw data for chart generation.

## 3. Edit scripts.js
- [ ] Remove analysis functions: `getNumericFields`, `groupAndCalculateStats`, `calculateGroupedStats`, etc.
- [ ] Simplify to only handle chart rendering and UI interactions using pre-computed data.

## 4. Testing
- [ ] Upload a sample file and verify chart generation works without client-side computation.
- [ ] Check data serialization for numpy/pandas types.
