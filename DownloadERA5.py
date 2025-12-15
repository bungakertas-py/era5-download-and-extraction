#%%
import os
print(os.path.exists(r"C:\Users\fsyuk\.cdsapirc"))
#%%
import os
import cdsapi

# ============================================================
# KONFIGURASI DASAR
# ============================================================

DATASET_SINGLE = "reanalysis-era5-single-levels"
DATASET_PLEVEL = "reanalysis-era5-pressure-levels"

# Variabel single level (nama resmi ERA5 di CDS)
ERA5_SINGLE_VARIABLES = [
    "10m_u_component_of_wind",
    "10m_v_component_of_wind",
    "2m_temperature",
    "surface_pressure",
    "total_precipitation",
    "mean_surface_downward_long_wave_radiation_flux",
    "cloud_base_height",
    "total_cloud_cover",
]

# Mapping ke nama file pendek (untuk nama ZIP)
VAR_SHORT_NAME = {
    "10m_u_component_of_wind": "u10",
    "10m_v_component_of_wind": "v10",
    "2m_temperature": "t2m",
    "surface_pressure": "sp",
    "total_precipitation": "tp",
    "mean_surface_downward_long_wave_radiation_flux": "msdwlwrf",
    "cloud_base_height": "cbh",
    "total_cloud_cover": "tcc",
}

# Variabel pressure level (RH @ 1000 hPa)
RH_VARIABLE = "relative_humidity"
RH_PRESSURE_LEVEL = ["1000"]

# Urutan tahun: 2024, 2023, 2022
YEARS = ["2024"]

# Base folder output — SEKARANG PAKAI WINDOWS PATH
BASE_DIR = r"C:\ERA5SEINDO"
os.makedirs(BASE_DIR, exist_ok=True)

# ============================================================
# SETUP CLIENT CDS
# ============================================================
client = cdsapi.Client()

# ============================================================
# PARAMETER UMUM REQUEST
# ============================================================

MONTHS = [
    "01", "02", "03",
    "04", "05", "06",
    "07", "08", "09",
    "10", "11", "12",
]

DAYS = [
    "01", "02", "03",
    "04", "05", "06",
    "07", "08", "09",
    "10", "11", "12",
    "13", "14", "15",
    "16", "17", "18",
    "19", "20", "21",
    "22", "23", "24",
    "25", "26", "27",
    "28", "29", "30",
    "31",
]

TIMES = [
    "00:00", "01:00", "02:00",
    "03:00", "04:00", "05:00",
    "06:00", "07:00", "08:00",
    "09:00", "10:00", "11:00",
    "12:00", "13:00", "14:00",
    "15:00", "16:00", "17:00",
    "18:00", "19:00", "20:00",
    "21:00", "22:00", "23:00",
]

# bbox seluruh Indonesia (+ sedikit margin)
AREA = [7.0, 94.0, -10.0, 142.0]   # [North, West, South, East]

# Template request untuk SINGLE LEVEL (ZIP)
COMMON_SINGLE = {
    "product_type": ["reanalysis"],
    "month": MONTHS,
    "day": DAYS,
    "time": TIMES,
    "data_format": "netcdf",
    "download_format": "zip",   # ZIP
    "area": AREA,
}

# Template request untuk PRESSURE LEVEL (RH 1000 hPa, ZIP)
COMMON_PLEVEL = {
    "product_type": ["reanalysis"],
    "month": MONTHS,
    "day": DAYS,
    "time": TIMES,
    "pressure_level": RH_PRESSURE_LEVEL,
    "data_format": "netcdf",
    "download_format": "zip",   # ZIP
    "area": AREA,
}

# ============================================================
# FUNGSI BANTU: DOWNLOAD ZIP DENGAN RETRY
# ============================================================

def robust_retrieve_zip(client, dataset, request, zip_target, max_retries=5):
    """
    Ambil data ke file ZIP dengan retry otomatis kalau error
    (misal 'File size mismatch').
    """
    attempt = 1
    while attempt <= max_retries:
        try:
            print(f"  [Attempt {attempt}/{max_retries}] retrieve {dataset} -> {zip_target}")
            r = client.retrieve(dataset, request)
            r.download(target=zip_target)
            print("  -> sukses download ZIP")
            return
        except Exception as e:
            print(f"  !! Error attempt {attempt}: {e}")
            # hapus file parsial
            if os.path.exists(zip_target):
                try:
                    os.remove(zip_target)
                except OSError:
                    pass
            attempt += 1

    raise RuntimeError(f"Gagal download {zip_target} setelah {max_retries} percobaan.")

# ============================================================
# LOOP TAHUN & VARIABEL
# ============================================================

for year in YEARS:
    year_dir = os.path.join(BASE_DIR, year)
    os.makedirs(year_dir, exist_ok=True)

    print("\n==============================")
    print(f"   PROSES TAHUN {year}")
    print("==============================")

    # --------- 1. SINGLE LEVEL VARIABEL ----------
    for var in ERA5_SINGLE_VARIABLES:
        short = VAR_SHORT_NAME[var]

        zip_path = os.path.join(year_dir, f"era5_single_{short}_{year}.zip")

        # Kalau ZIP sudah ada, skip (biar kalau rerun nggak ulang)
        if os.path.exists(zip_path):
            print(f"\nFile {zip_path} sudah ada, skip.")
            continue

        request_single = dict(COMMON_SINGLE)
        request_single["year"] = [year]
        request_single["variable"] = [var]

        print(f"\n=== Download SINGLE-LEVEL: {var} ({year}) ===")
        print(f"-> ZIP : {zip_path}")

        robust_retrieve_zip(client, DATASET_SINGLE, request_single, zip_path)

    # --------- 2. PRESSURE LEVEL RH @ 1000 hPa ----------
    rh_zip_path = os.path.join(year_dir, f"era5_plevel_rh1000_{year}.zip")

    if not os.path.exists(rh_zip_path):
        request_rh = dict(COMMON_PLEVEL)
        request_rh["year"] = [year]
        request_rh["variable"] = [RH_VARIABLE]

        print(f"\n=== Download PRESSURE-LEVEL: {RH_VARIABLE} 1000 hPa ({year}) ===")
        print(f"-> ZIP : {rh_zip_path}")

        robust_retrieve_zip(client, DATASET_PLEVEL, request_rh, rh_zip_path)
    else:
        print(f"\nFile {rh_zip_path} sudah ada, skip.")

print("\nSelesai download ERA5 (ZIP single-level + ZIP RH1000) untuk 2024, 2023, 2022.")
