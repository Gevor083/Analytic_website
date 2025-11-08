# TODO: Add "View All Data" Button and Move Filter/Sort to Full Data Page

## Steps to Complete:
- [x] Create full_data_view in analytics_app/views.py: Load DataFrame, limit to 1000 rows, pass to template.
- [x] Add URL pattern for full_data_view in analytics_app/urls.py.
- [x] Add "View All Data" button in data preview section of analytics_app/templates/analytics_app/result.html.
- [x] Create analytics_app/templates/analytics_app/full_data.html template: Display full data table with horizontal scroll, include filter and sort options.
- [x] Remove filter and sort options from chart builder modal in result.html.
- [x] Update JavaScript in result.html to remove filter/sort handling from chart modal.
- [x] Test the new functionality: Button opens new window with full data, filter/sort work on full data page.
