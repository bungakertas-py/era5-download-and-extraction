#%%
import os
import xarray as xr

# ============================================
# INPUT FOLDER & TAHUN
# ============================================

BASE_DIR = input(
    "Folder dasar ERA5 (enter untuk default C:\\ERA5SEINDO): "
).strip() or r"C:\ERA5SEINDO"

if not os.path.isdir(BASE_DIR):
    raise FileNotFoundError(f"Folder dasar tidak ditemukan: {BASE_DIR}")

# Cari subfolder tahun
year_dirs = sorted(
    d for d in os.listdir(BASE_DIR) if os.path.isdir(os.path.join(BASE_DIR, d))
)

if not year_dirs:
    raise FileNotFoundError(f"Tidak ada subfolder tahun di {BASE_DIR}")

print("Tahun yang tersedia:")
for y in year_dirs:
    print(" -", y)

year = input("Pilih tahun yang ingin dicek (contoh 2024): ").strip()
if year not in year_dirs:
    raise ValueError(f"Tahun {year} tidak ditemukan. Pilihan: {year_dirs}")

year_folder = os.path.join(BASE_DIR, year)
print(f"\nFolder tahun yang dicek: {year_folder}")

# ============================================
# CEK SEMUA FILE .NC DI FOLDER TAHUN
# ============================================

nc_files = [f for f in os.listdir(year_folder) if f.lower().endswith(".nc")]

if not nc_files:
    raise FileNotFoundError(f"Tidak ada file .nc di {year_folder}")

for fname in sorted(nc_files):
    fpath = os.path.join(year_folder, fname)
    print("\n" + "=" * 80)
    print(f"FILE : {fname}")
    print("=" * 80)

    try:
        ds = xr.open_dataset(fpath)
    except Exception as e:
        print(f"  !! GAGAL BUKA FILE: {e}")
        continue

    # Print ringkasan xarray
    print(ds)

    # Info time
    if "time" in ds.coords or "time" in ds.dims:
        try:
            t = ds["time"]
            print("\n  Time range :",
                  str(t[0].values), "sampai", str(t[-1].values))
            print("  Jumlah time:", t.size)
        except Exception as e:
            print("  (Gagal baca koordinat waktu:", e, ")")

    # Info latitude / longitude
    lat_name = None
    lon_name = None
    for cand in ["latitude", "lat"]:
        if cand in ds.coords:
            lat_name = cand
            break
    for cand in ["longitude", "lon"]:
        if cand in ds.coords:
            lon_name = cand
            break

    if lat_name is not None and lon_name is not None:
        lat = ds[lat_name]
        lon = ds[lon_name]
        print(f"  Latitude : {float(lat.min())} s.d. {float(lat.max())} (n={lat.size})")
        print(f"  Longitude: {float(lon.min())} s.d. {float(lon.max())} (n={lon.size})")

    ds.close()

print("\nSelesai cek semua file .nc di tahun", year)
#%%
import os
import numpy as np
import pandas as pd
import xarray as xr

# ==========================
# INPUT & KONFIGURASI
# ==========================

BASE_DIR = input(
    "Folder dasar ERA5 (enter untuk default C:\\ERA5SEINDO): "
).strip() or r"C:\ERA5SEINDO"

if not os.path.isdir(BASE_DIR):
    raise FileNotFoundError(f"Folder dasar tidak ditemukan: {BASE_DIR}")

# Cari subfolder tahun
year_dirs = sorted(
    d for d in os.listdir(BASE_DIR) if os.path.isdir(os.path.join(BASE_DIR, d))
)
if not year_dirs:
    raise FileNotFoundError(f"Tidak ada subfolder tahun di {BASE_DIR}")

print("Tahun yang tersedia:")
for y in year_dirs:
    print(" -", y)

year = input("Pilih tahun yang ingin diekstrak (contoh 2024): ").strip()
if year not in year_dirs:
    raise ValueError(f"Tahun {year} tidak ditemukan. Pilihan: {year_dirs}")

year_folder = os.path.join(BASE_DIR, year)

lon_input = float(input("Longitude lokasi (derajat, misal 104.0): "))
lat_input = float(input("Latitude lokasi (derajat, misal 1.0): "))

print(f"\nAkan diproses: tahun {year}, titik lon={lon_input}, lat={lat_input}")
print(f"Folder data: {year_folder}")

# mapping file -> nama variabel di dalam file
FILE_VAR_MAP = {
    "u10":      ("u10.nc",       "u10"),
    "v10":      ("v10.nc",       "v10"),
    "t2m":      ("t2m.nc",       "t2m"),
    "sp":       ("sp.nc",        "sp"),
    "tp":       ("tp.nc",        "tp"),
    "tcc":      ("tcc.nc",       "tcc"),
    "cbh":      ("cbh.nc",       "cbh"),
    "rad":      ("msdwlwrf.nc",  "avg_sdlwrf"),  # radiasi
    "rh":       ("r.nc",         "r"),           # relative humidity
}

# ==========================
# FUNGSI BANTU
# ==========================

def open_da(path, varname, select_pl_1000=False):
    """
    Buka DataArray varname dari file path.
    - Drop dimensi 'number' (ambil index 0 kalau ada)
    - Kalau select_pl_1000=True dan ada 'pressure_level',
      pilih level 1000 hPa (kalau ada) atau level pertama.
    """
    if not os.path.isfile(path):
        raise FileNotFoundError(f"File tidak ditemukan: {path}")

    ds = xr.open_dataset(path)

    if varname not in ds.data_vars:
        ds.close()
        raise KeyError(f"Variabel '{varname}' tidak ditemukan di {path}")

    da = ds[varname]

    # hilangkan dimensi 'number' kalau ada
    if "number" in da.dims:
        da = da.isel(number=0)

    # khusus pressure_level (RH)
    if select_pl_1000 and "pressure_level" in da.dims:
        if 1000 in da["pressure_level"]:
            da = da.sel(pressure_level=1000)
        else:
            da = da.isel(pressure_level=0)

    ds.close()
    return da


def wind_speed_direction(u, v):
    # u, v bisa array NumPy
    speed = np.sqrt(u**2 + v**2)
    direction = (180.0 + np.degrees(np.arctan2(u, v))) % 360.0
    return speed, direction


# ==========================
# BACA STRUKTUR DARI u10.nc
# ==========================

u10_path, u10_var = FILE_VAR_MAP["u10"]
u10_path = os.path.join(year_folder, u10_path)

print(f"\nDeteksi struktur dari: {u10_path}")
da_u10 = open_da(u10_path, u10_var, select_pl_1000=False)

# di file kamu: waktu = 'valid_time', lat/lon = 'latitude'/'longitude'
time_name = "valid_time"
lat_name = "latitude"
lon_name = "longitude"

# titik grid terdekat untuk u10
point_u10 = da_u10.sel(
    {lat_name: lat_input, lon_name: lon_input}, method="nearest"
)

time_index = pd.to_datetime(point_u10[time_name].values)
lat_grid = float(point_u10[lat_name].values)
lon_grid = float(point_u10[lon_name].values)
print(f"  Titik grid terdekat: lon={lon_grid}, lat={lat_grid}")
print(f"  Jumlah time: {len(time_index)}")

# ==========================
# BACA VARIABEL LAIN
# ==========================

print("\nMembaca semua variabel lain...")

da_dict = {"u10": da_u10}

for key in ["v10", "t2m", "sp", "tp", "tcc", "cbh", "rad", "rh"]:
    fname, vname = FILE_VAR_MAP[key]
    fpath = os.path.join(year_folder, fname)
    print(f"  {key}: {fpath} (var='{vname}')")
    if key == "rh":
        da = open_da(fpath, vname, select_pl_1000=True)
    else:
        da = open_da(fpath, vname, select_pl_1000=False)
    da_dict[key] = da

# ==========================
# EXTRACT TIMESERIES PER VAR
# ==========================

def extract_series(da):
    """ambil deret waktu di titik lat_grid/lon_grid."""
    p = da.sel({lat_name: lat_grid, lon_name: lon_grid}, method="nearest")
    return p.values

# u & v angin
u = extract_series(da_dict["u10"])
v = extract_series(da_dict["v10"])
speed, direction = wind_speed_direction(u, v)

# tutupan awan
tcc_val = extract_series(da_dict["tcc"])

# suhu
t2m_val = extract_series(da_dict["t2m"])

# RH
rh_val = extract_series(da_dict["rh"])

# tekanan (Pa -> hPa)
sp_val = extract_series(da_dict["sp"]) / 100.0

# ketinggian awan
cbh_val = extract_series(da_dict["cbh"])

# hujan (m -> mm)
tp_val = extract_series(da_dict["tp"]) * 1000.0

# radiasi
rad_val = extract_series(da_dict["rad"])

# ==========================
# BANGUN DATAFRAME & SIMPAN
# ==========================

df = pd.DataFrame(index=time_index)
df["Year"] = df.index.year
df["Month"] = df.index.month
df["Day"] = df.index.day
df["Hour"] = df.index.hour

df["TutupanAwan"]   = tcc_val
df["Temperature"]   = t2m_val - 273.15        # kalau mau °C: t2m_val - 273.15
df["RH"]            = rh_val
df["Tekanan"]       = sp_val
df["ArahAngin"]     = direction
df["KecAngin"]      = speed
df["KetinggianAwan"]= cbh_val
df["Hujan"]         = tp_val
df["Radiasi"]       = rad_val

# urutkan kolom sesuai permintaan
df_out = df[
    [
        "Year",
        "Month",
        "Day",
        "Hour",
        "TutupanAwan",
        "Temperature",
        "RH",
        "Tekanan",
        "ArahAngin",
        "KecAngin",
        "KetinggianAwan",
        "Hujan",
        "Radiasi",
    ]
]

out_name = f"ERA5_Point_{year}_lon{lon_input:.2f}_lat{lat_input:.2f}.xlsx"
out_path = os.path.join(year_folder, out_name)
df_out.to_excel(out_path, index=False)

print(f"\nSelesai. File Excel disimpan di:\n{out_path}")
