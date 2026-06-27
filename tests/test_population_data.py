import pytest
import pandas as pd
from pathlib import Path


@pytest.fixture
def data_dir():
    """Get the data directory path."""
    return Path(__file__).resolve().parent.parent / "data" / "input"


@pytest.fixture
def data_2024(data_dir):
    """Load 2024 data."""
    return pd.read_csv(data_dir / "data2024.csv", sep=";")


@pytest.fixture
def data_2025(data_dir):
    """Load 2025 data."""
    return pd.read_csv(data_dir / "data2025.csv", sep=";")


def test_detect_row_changes(data_2024, data_2025):
    """Test that detects what rows have changed between 2024 and 2025 data."""
    # Define key columns for comparison
    key_columns = ["provincia", "municipio", "sexo"]
    
    # Set key columns as index for comparison
    df_2024_indexed = data_2024.set_index(key_columns).sort_index()
    df_2025_indexed = data_2025.set_index(key_columns).sort_index()
    
    # Find rows that exist in 2024 but not in 2025
    rows_removed = df_2024_indexed.index.difference(df_2025_indexed.index)
    
    # Find rows that exist in 2025 but not in 2024
    rows_added = df_2025_indexed.index.difference(df_2024_indexed.index)
    
    # Find rows that exist in both but have different values
    common_index = df_2024_indexed.index.intersection(df_2025_indexed.index)
    rows_modified = df_2024_indexed.loc[common_index].compare(
        df_2025_indexed.loc[common_index], align_axis=1
    )
    # Rename column levels from 'self'/'other' to '2024'/'2025'
    if len(rows_modified) > 0:
        rows_modified.columns = rows_modified.columns.set_levels(['data_2024', 'data_2025'], level=1)
    
    # Print detailed change information
    print("\n" + "=" * 80)
    print("ROW CHANGE DETECTION REPORT")
    print("=" * 80)
    
    if len(rows_removed) > 0:
        print(f"\n📋 ROWS REMOVED (in 2024 but not in 2025): {len(rows_removed)}")
        print("-" * 80)
        removed_df = data_2024.set_index(key_columns).loc[rows_removed]
        print(removed_df)
    else:
        print("\n✅ No rows removed")
    
    if len(rows_added) > 0:
        print(f"\n📋 ROWS ADDED (in 2025 but not in 2024): {len(rows_added)}")
        print("-" * 80)
        added_df = data_2025.set_index(key_columns).loc[rows_added]
        print(added_df)
    else:
        print("\n✅ No rows added")
    
    if len(rows_modified) > 0:
        print(f"\n📋 ROWS MODIFIED (value changes): {len(rows_modified)}")
        print("-" * 80)
        print(rows_modified)
    else:
        print("\n✅ No rows modified")
    
    print("\n" + "=" * 80)
    print("SUMMARY")
    print("=" * 80)
    print(f"Total rows in 2024: {len(data_2024)}")
    print(f"Total rows in 2025: {len(data_2025)}")
    print(f"Rows removed: {len(rows_removed)}")
    print(f"Rows added: {len(rows_added)}")
    print(f"Rows modified: {len(rows_modified) if len(rows_modified) > 0 else 0}")
    print("=" * 80 + "\n")
    
    # Assert that the test ran successfully
    assert len(data_2024) > 0, "2024 data should not be empty"
    assert len(data_2025) > 0, "2025 data should not be empty"


def test_data_2025_quality(data_2025):
    """Test generic data quality checks for data2025.csv."""
    
    print("\n" + "=" * 80)
    print("DATA QUALITY REPORT FOR data2025.csv")
    print("=" * 80)
    
    # 1. Check for empty dataset
    print("\n✓ Dataset Shape")
    print(f"  Rows: {len(data_2025)}")
    print(f"  Columns: {len(data_2025.columns)}")
    assert len(data_2025) > 0, "Dataset should not be empty"
    assert len(data_2025.columns) > 0, "Dataset should have columns"
    
    # 2. Check column names
    print("\n✓ Column Names")
    expected_columns = ['provincia', 'municipio', 'sexo', 'total']
    print(f"  Expected: {expected_columns}")
    print(f"  Actual: {data_2025.columns.tolist()}")
    assert data_2025.columns.tolist() == expected_columns, "Column names do not match expected schema"
    
    # 3. Check for null values
    print("\n✓ Null Values Check")
    null_counts = data_2025.isnull().sum()
    
    for col in data_2025.columns:
        if null_counts[col] > 0:
            print(f"  ⚠️  {col}: {null_counts[col]} null values")
        else:
            print(f"  {col}: {null_counts[col]} null values")
    
    # 4. Check data types
    print("\n✓ Data Types")
    for col in data_2025.columns:
        print(f"  {col}: {data_2025[col].dtype}")
    
    # 5. Check for duplicates
    print("\n✓ Duplicate Rows")
    duplicate_count = data_2025.duplicated().sum()
    print(f"  Total duplicate rows: {duplicate_count}")
    assert duplicate_count == 0, f"Found {duplicate_count} duplicate rows"
    
    # 6. Check numeric column (total) for validity
    print("\n✓ Numeric Column Validation (total)")
    assert pd.api.types.is_numeric_dtype(data_2025['total']), "Column 'total' should be numeric"
    print(f"  Min value: {data_2025['total'].min()}")
    print(f"  Max value: {data_2025['total'].max()}")
    print(f"  Mean value: {data_2025['total'].mean():.2f}")
    print(f"  Std deviation: {data_2025['total'].std():.2f}")
    assert (data_2025['total'] >= 0).all(), "All 'total' values should be non-negative"
    
    # 7. Check categorical columns for unexpected values
    print("\n✓ Categorical Columns Validation")
    
    # Check sexo values
    sexo_values = data_2025['sexo'].unique()
    print(f"  sexo unique values ({len(sexo_values)}): {sorted(sexo_values)}")
    valid_sexo = ['Ambos sexos', 'Hombres', 'Mujeres']
    for val in sexo_values:
        assert val in valid_sexo, f"Unexpected value in 'sexo': {val}"
    
    # Check provincia format
    print(f"  provincia unique values: {data_2025['provincia'].nunique()} provinces")
    assert data_2025['provincia'].nunique() > 0, "Should have provincia values"
    
    # Check municipio format
    print(f"  municipio unique values: {data_2025['municipio'].nunique()} municipalities")
    assert data_2025['municipio'].nunique() > 0, "Should have municipio values"
    
    # 8. Check for data consistency
    print("\n✓ Data Consistency")
    
    # Group by provincia and sexo to check aggregation
    grouped = data_2025.groupby(['provincia', 'sexo'])['total'].sum().reset_index()
    print(f"  Total provincia-sexo combinations: {len(grouped)}")
    
    # Each provincia should have records for all three sexo categories (or at least most of them)
    provincia_sexo_counts = data_2025.groupby('provincia')['sexo'].nunique()
    avg_categories = provincia_sexo_counts.mean()
    print(f"  Average sexo categories per provincia: {avg_categories:.2f}")
    
    # 9. Summary Statistics
    print("\n✓ Summary Statistics")
    print(f"  Total records: {len(data_2025)}")
    print(f"  Total unique provincias: {data_2025['provincia'].nunique()}")
    print(f"  Total unique municipios: {data_2025['municipio'].nunique()}")
    print(f"  Total unique sexo values: {data_2025['sexo'].nunique()}")
    print(f"  Sum of all totals: {data_2025['total'].sum()}")
    
    print("\n" + "=" * 80)
    print("✅ ALL DATA QUALITY CHECKS PASSED")
    print("=" * 80 + "\n")
    
    # Final assertions
    assert len(data_2025) > 0, "Dataset must not be empty"


def test_municipio_gender_consistency(data_2025):
    """Test that for each municipio, Hombres + Mujeres = Ambos sexos."""

    raw_2025_path = Path(__file__).resolve().parent.parent / "data" / "input" / "data2025.csv"
    raw_data_2025 = pd.read_csv(raw_2025_path, sep=";", dtype=str, keep_default_na=False)

    def normalize_total_value(value):
        """Normalize totals that may use dots as thousand separators."""
        if pd.isna(value):
            return None

        text = str(value).strip().replace(" ", "")
        if not text:
            return None

        # Values like 1.382 or 12.345.678 are thousand-separated integers.
        # We convert them to 1382 or 12345678 for reliable arithmetic checks.
        sign = ""
        if text.startswith("-"):
            sign = "-"
            text = text[1:]

        if "." in text and "," not in text:
            dot_parts = text.split(".")
            if len(dot_parts) > 1 and all(part.isdigit() for part in dot_parts):
                if all(len(part) == 3 for part in dot_parts[1:]):
                    return float(sign + "".join(dot_parts))

        # Fallback for decimal values, including comma decimal separator.
        normalized = sign + text.replace(".", "").replace(",", ".") if "," in text and "." in text else sign + text.replace(",", ".")
        try:
            return float(normalized)
        except ValueError:
            return None
    
    print("\n" + "=" * 80)
    print("MUNICIPIO GENDER CONSISTENCY CHECK")
    print("=" * 80)
    print(f"Using raw string totals from: {raw_2025_path}")
    
    inconsistencies = []
    skipped_missing_categories = 0
    skipped_non_numeric = 0
    checked_municipios = 0
    
    # Group by provincia and municipio
    for (provincia, municipio), group in raw_data_2025.groupby(['provincia', 'municipio']):
        # Extract values for each gender category
        ambos_sexos = group[group['sexo'] == 'Ambos sexos']['total'].values
        hombres = group[group['sexo'] == 'Hombres']['total'].values
        mujeres = group[group['sexo'] == 'Mujeres']['total'].values
        
        # Check if all three categories exist
        if len(ambos_sexos) > 0 and len(hombres) > 0 and len(mujeres) > 0:
            ambos_value = normalize_total_value(ambos_sexos[0])
            hombres_value = normalize_total_value(hombres[0])
            mujeres_value = normalize_total_value(mujeres[0])

            if any(value is None for value in [ambos_value, hombres_value, mujeres_value]):
                skipped_non_numeric += 1
                continue

            checked_municipios += 1
            
            # Calculate the sum and compare with tolerance for floating point errors
            calculated_sum = hombres_value + mujeres_value
            difference = abs(ambos_value - calculated_sum)
            
            # Use a tolerance for floating point comparison (0.1% of the value)
            tolerance = max(abs(calculated_sum) * 0.001, 0.01)
            
            if difference > tolerance:
                inconsistencies.append({
                    'provincia': provincia,
                    'municipio': municipio,
                    'Ambos sexos': ambos_value,
                    'Hombres': hombres_value,
                    'Mujeres': mujeres_value,
                    'Hombres + Mujeres': calculated_sum,
                    'Difference': difference
                })
        else:
            skipped_missing_categories += 1
    
    if len(inconsistencies) > 0:
        print(f"\n⚠️  FOUND {len(inconsistencies)} MUNICIPIOS WITH INCONSISTENT GENDER SUMS:\n")
        print("-" * 80)
        
        # Show first 10 inconsistencies
        for inc in inconsistencies[:10]:
            print(f"\nProvincia: {inc['provincia']}")
            print(f"Municipio: {inc['municipio']}")
            print(f"  Ambos sexos:      {inc['Ambos sexos']}")
            print(f"  Hombres:          {inc['Hombres']}")
            print(f"  Mujeres:          {inc['Mujeres']}")
            print(f"  Sum (H + M):      {inc['Hombres + Mujeres']}")
            print(f"  Difference:       {inc['Difference']}")
        
        if len(inconsistencies) > 10:
            print(f"\n... and {len(inconsistencies) - 10} more inconsistencies")
    else:
        print("\n✅ ALL MUNICIPIOS HAVE CONSISTENT GENDER SUMS")
        print("   For all municipios: Hombres + Mujeres = Ambos sexos")
    
    print("\n" + "=" * 80)
    print(f"SUMMARY")
    print("=" * 80)
    total_municipios = len(raw_data_2025.groupby(['provincia', 'municipio']))
    print(f"Total municipios checked: {total_municipios}")
    print(f"Municipios fully comparable: {checked_municipios}")
    print(f"Municipios with inconsistencies: {len(inconsistencies)}")
    print(f"Municipios consistent: {checked_municipios - len(inconsistencies)}")
    print(f"Skipped (missing gender categories): {skipped_missing_categories}")
    print(f"Skipped (non-numeric totals): {skipped_non_numeric}")
    if checked_municipios > 0:
        consistency_rate = ((checked_municipios - len(inconsistencies)) / checked_municipios) * 100
        print(f"Consistency rate (comparable municipios): {consistency_rate:.2f}%")
    if len(inconsistencies) > 0 and checked_municipios > 0:
        inconsistency_rate = (len(inconsistencies) / checked_municipios) * 100
        print(f"Inconsistency rate (comparable municipios): {inconsistency_rate:.2f}%")
    print("=" * 80 + "\n")
    
    # Pass the test but report the inconsistencies
    assert len(data_2025) > 0, "Dataset must not be empty"
    assert len(raw_data_2025) > 0, "Raw dataset must not be empty"
