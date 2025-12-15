# era5-download-and-extraction
Python workflow for automated ERA5 data retrieval and extraction into station-based time series for further meteorological analysis.
================================
README – ERA5 Download and Point Extraction Workflow
====================================================

This repository contains two Python scripts for downloading ERA5 reanalysis data from the Copernicus Climate Data Store (CDS) and extracting time series at a specific point into an Excel file.

Scripts:

* DownloadERA5.py – downloads ERA5 data (single-level + pressure-level RH) as ZIP files.
* EkstrakDataNc.py – inspects NetCDF files and extracts point-based time series from ERA5 into an Excel file.

================================
1. Prerequisites
================

1.1. Software

* Python 3.x
* Required Python packages:

  * cdsapi
  * xarray
  * numpy
  * pandas

Example installation:

pip install cdsapi xarray numpy pandas

1.2. CDS API Configuration

To access ERA5, you must have a Copernicus Climate Data Store (CDS) account and set up your API key:

1. Register at the CDS website and create an API key.
2. Create a file called ".cdsapirc" in your user home directory, for example on Windows:
   C:\Users<USERNAME>.cdsapirc
3. Paste your CDS API key configuration into that file.

In DownloadERA5.py there is a quick check like:

print(os.path.exists(r"C:\Users\fsyuk.cdsapirc"))

You can adjust this path to your own username if needed.

================================
2. Folder Structure and Data Layout
===================================

Both scripts assume a base folder for ERA5 data on Windows:

C:\ERA5SEINDO\

Under this base directory, the scripts use one subfolder per year, for example:

C:\ERA5SEINDO
└── 2024
├── era5_single_u10_2024.zip
├── era5_single_v10_2024.zip
├── ...
└── era5_plevel_rh1000_2024.zip

Note:

* The downloader script saves ZIP files.
* You need to unzip them manually (or via another script) so that EkstrakDataNc.py can read the .nc files.
* The extraction script expects NetCDF files with names such as "u10.nc", "t2m.nc", "sp.nc", etc.

================================
3. Script 1 – DownloadERA5.py (ERA5 Downloader)
===============================================

3.1. Purpose

This script downloads:

* ERA5 single-level variables (e.g. 10 m wind, 2 m temperature, surface pressure, etc.)
* ERA5 pressure-level variable: relative humidity at 1000 hPa

for a user-defined list of years over a fixed domain covering Indonesia, and stores them as ZIP of NetCDF per variable per year.

3.2. Main Configuration

Datasets:

* DATASET_SINGLE = "reanalysis-era5-single-levels"
* DATASET_PLEVEL = "reanalysis-era5-pressure-levels"

Single-level variables (ERA5 names):

* 10m_u_component_of_wind
* 10m_v_component_of_wind
* 2m_temperature
* surface_pressure
* total_precipitation
* mean_surface_downward_long_wave_radiation_flux
* cloud_base_height
* total_cloud_cover

Short names for file naming, for example:

* "10m_u_component_of_wind" -> "u10"
* "2m_temperature" -> "t2m"

These are used to build file names such as:

* era5_single_u10_2024.zip
* era5_single_t2m_2024.zip

Pressure-level configuration:

* Variable: relative_humidity
* Pressure level: 1000 hPa
* Saved as: era5_plevel_rh1000_<year>.zip

Years:

* YEARS = ["2024"] by default
* You can add other years, e.g. ["2022", "2023", "2024"]

Geographic domain (AREA) used for all downloads:

AREA = [North, West, South, East]
AREA = [7.0, 94.0, -10.0, 142.0]

This roughly covers the whole of Indonesia plus some margin.

Time coverage:

* Months: 01–12
* Days: 01–31
* Hours: 00:00–23:00

3.3. Request Templates

The script defines base dictionaries:

* COMMON_SINGLE – template for single-level ERA5 requests
* COMMON_PLEVEL – template for pressure-level RH requests

Both include:

* product_type = "reanalysis"
* month, day, time arrays
* data_format = "netcdf"
* download_format = "zip"
* area = AREA

These templates are copied and extended with specific "year" and "variable" inside the main loop.

3.4. Robust Download Function

robust_retrieve_zip(...):

* Wraps the CDS client.retrieve() and client.download() calls with a retry mechanism.
* Tries up to max_retries times (default 5).
* If an error occurs (network issue, size mismatch, etc.), it:

  * Prints the error message.
  * Deletes any partially downloaded file.
  * Retries until the maximum number of attempts is reached.

If all retries fail, it raises a RuntimeError.

3.5. Main Loop

For each "year" in YEARS:

1. Create a subfolder:
   C:\ERA5SEINDO<year>\

2. For each single-level variable:

   * Build zip_path = era5_single_<short>_<year>.zip
   * If the ZIP already exists, skip.
   * Construct the full request from COMMON_SINGLE + year + variable.
   * Download with robust_retrieve_zip(...).

3. For pressure-level RH:

   * Build rh_zip_path = era5_plevel_rh1000_<year>.zip
   * If not present, build request_rh from COMMON_PLEVEL and download.

At the end, the script prints a message indicating completion for all requested years.

================================
4. Script 2 – EkstrakDataNc.py (NetCDF Inspection & Point Extraction)
=====================================================================

This script contains two main parts:

1. NetCDF inspection utility – prints dataset structure and basic info for all .nc files in a given year folder.
2. Point-based extractor – extracts ERA5 time series at a specific latitude/longitude and saves them as an Excel file.

4.1. Part 1 – Inspect NetCDF Files

This section:

1. Asks for the base directory (C:\ERA5SEINDO by default).
2. Lists available year subfolders and lets the user choose a year.
3. Scans the chosen year folder for all .nc files.
4. For each .nc file:

   * Opens with xarray.open_dataset().
   * Prints the dataset summary (ds).
   * If "time" is present, prints:

     * Start and end time
     * Number of time steps
   * If "latitude"/"longitude" (or "lat"/"lon") coordinates are present, prints:

     * Min and max lat/lon
     * Grid sizes

This helps you quickly verify:

* Time coverage
* Spatial domain
* Variable names and dimensions

4.2. Part 2 – Extract Point Time Series to Excel

This is the main extraction workflow.

4.2.1. Inputs

The script asks the user for:

1. Base ERA5 folder (default: C:\ERA5SEINDO).
2. Year (must be an existing subfolder, e.g. 2024).
3. Longitude (e.g. 104.0).
4. Latitude (e.g. 1.0).

It then:

* Confirms the folder and year.
* Prints a message describing what will be processed.

4.2.2. Expected NetCDF Files and Variable Names

The script uses a mapping:

FILE_VAR_MAP = {
"u10": ("u10.nc",      "u10"),
"v10": ("v10.nc",      "v10"),
"t2m": ("t2m.nc",      "t2m"),
"sp":  ("sp.nc",       "sp"),
"tp":  ("tp.nc",       "tp"),
"tcc": ("tcc.nc",      "tcc"),
"cbh": ("cbh.nc",      "cbh"),
"rad": ("msdwlwrf.nc", "avg_sdlwrf"),  # radiation
"rh":  ("r.nc",        "r"),           # relative humidity
}

This means the year folder should contain NetCDF files with these names and internal variable names.
If your file names differ, adjust FILE_VAR_MAP accordingly.

4.2.3. Helper Functions

1. open_da(path, varname, select_pl_1000=False):

   * Opens a dataset and returns the requested variable as a DataArray.
   * If the variable has a "number" dimension (e.g. ensemble), it selects the first member.
   * If select_pl_1000=True and there is a "pressure_level" dimension, it tries to select 1000 hPa; otherwise, it selects the first level. Used for RH.

2. wind_speed_direction(u, v):

   * Computes wind speed and direction from u and v components:

     * Speed = sqrt(u² + v²)
     * Direction = meteorological direction (0–360°).

4.2.4. Grid Detection and Coordinate Names

The script first opens "u10.nc" and:

* Assumes time coordinate name: "valid_time".
* Assumes spatial coordinates: "latitude" and "longitude".

It then selects the nearest grid point to the user-specified lon/lat using method="nearest" and prints:

* The actual grid point longitude and latitude.
* The number of available time steps.

If your ERA5 files use different coordinate names (e.g. "time", "lat", "lon"), you can modify:

* time_name
* lat_name
* lon_name

accordingly in the script.

4.2.5. Reading All Variables

For each key in FILE_VAR_MAP, the script:

* Builds the file path (e.g. C:\ERA5SEINDO\2024\u10.nc).
* Opens the dataset and extracts the relevant DataArray.
* For RH, it also selects the 1000 hPa level when available.

4.2.6. Extracting Time Series at the Point

A helper function extract_series(da) selects data at the previously determined nearest grid point (lat_grid, lon_grid) and returns the time series as a NumPy array.

The script derives at that grid point:

* Wind speed and direction from u10 and v10.
* Cloud cover (tcc).
* 2 m temperature (t2m).
* Relative humidity (rh).
* Surface pressure (sp), converted from Pa to hPa.
* Cloud base height (cbh).
* Total precipitation (tp), converted from m to mm.
* Radiation (rad).

4.2.7. Building the Output DataFrame

Using time_index as the index, the script builds a pandas.DataFrame with:

Time metadata:

* Year
* Month
* Day
* Hour

Meteorological variables:

* TutupanAwan     – total cloud cover
* Temperature     – 2 m temperature in °C (t2m - 273.15)
* RH              – relative humidity (from RH at 1000 hPa)
* Tekanan         – surface pressure in hPa
* ArahAngin       – wind direction (degrees)
* KecAngin        – wind speed (m/s)
* KetinggianAwan  – cloud base height
* Hujan           – precipitation (mm)
* Radiasi         – downward longwave radiation flux (units as in input)

The columns are explicitly ordered and then written to an Excel file.

4.2.8. Output File Naming

The output Excel file name format is:

ERA5_Point_<year>_lon<lon>_lat<lat>.xlsx

For example:

ERA5_Point_2024_lon104.00_lat1.00.xlsx

The file is saved in the selected year folder:

C:\ERA5SEINDO<year>\ERA5_Point_<year>_lon<lon>_lat<lat>.xlsx

A completion message prints the full path.

================================
5. Typical Workflow
===================

1. Set up CDS API (.cdsapirc) and install required packages.
2. Run DownloadERA5.py:

   * Adjust YEARS if needed.
   * Check that ZIP files are created in C:\ERA5SEINDO<year>.
3. Unzip the downloaded ZIP files for each year and rename NetCDF files to match FILE_VAR_MAP if necessary (e.g. u10.nc, t2m.nc, etc.).
4. (Optional) Run the NetCDF inspection part of EkstrakDataNc.py to verify:

   * Time range and grid extent.
   * Variable names and coordinate names.
5. Run the extraction part of EkstrakDataNc.py:

   * Provide base directory, year, longitude, and latitude when prompted.
   * The script creates an Excel file containing the full time series at the nearest grid point.

================================
6. Notes and Troubleshooting
============================

* File not found errors:

  * Ensure your unzipped NetCDF file names match those in FILE_VAR_MAP.
  * Ensure that the base folder and year folder exist.

* Coordinate mismatches:

  * If your NetCDF files use "time", "lat", "lon" instead of "valid_time", "latitude", "longitude", update:

    * time_name
    * lat_name
    * lon_name
      in the script.

* Pressure level selection (RH):

  * If the file does not include 1000 hPa, the script falls back to the first available pressure level.

* Units:

  * Temperature is converted from Kelvin to Celsius.
  * Surface pressure from Pa to hPa.
  * Precipitation from meters to millimeters.
  * Other variables retain the original ERA5 units.
