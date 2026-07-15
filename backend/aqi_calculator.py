# This file contains all the logic for calculating AQI based on CPCB standards.

# --- 1. Indian CPCB Breakpoint Tables ---
# (Pollutant, AQI-Low, AQI-High, Conc-Low, Conc-High)
PM25_BREAKPOINTS = [
    (0, 50, 0, 30),
    (51, 100, 31, 60),
    (101, 200, 61, 90),
    (201, 300, 91, 120),
    (301, 400, 121, 250),
    (401, 500, 251, 1000) # Assuming 500+ maps to 251+
]
PM10_BREAKPOINTS = [
    (0, 50, 0, 50),
    (51, 100, 51, 100),
    (101, 200, 101, 250),
    (201, 300, 251, 350),
    (301, 400, 351, 430),
    (401, 500, 431, 2000)
]
CO_BREAKPOINTS = [ # Note: CO is in mg/m³, not µg/m³
    (0, 50, 0, 1.0),
    (51, 100, 1.1, 2.0),
    (101, 200, 2.1, 10.0),
    (201, 300, 10.1, 17.0),
    (301, 400, 17.1, 34.0),
    (401, 500, 34.1, 100.0)
]
O3_BREAKPOINTS = [
    (0, 50, 0, 50),
    (51, 100, 51, 100),
    (101, 200, 101, 168),
    (201, 300, 169, 208),
    (301, 400, 209, 748),
    (401, 500, 749, 2000)
]
NO2_BREAKPOINTS = [
    (0, 50, 0, 40),
    (51, 100, 41, 80),
    (101, 200, 81, 180),
    (201, 300, 181, 280),
    (301, 400, 281, 400),
    (401, 500, 401, 2000)
]
SO2_BREAKPOINTS = [
    (0, 50, 0, 40),
    (51, 100, 41, 80),
    (101, 200, 81, 380),
    (201, 300, 381, 800),
    (301, 400, 801, 1600),
    (401, 500, 1601, 3000)
]
NH3_BREAKPOINTS = [
    (0, 50, 0, 200),
    (51, 100, 201, 400),
    (101, 200, 401, 800),
    (201, 300, 801, 1200),
    (301, 400, 1201, 1800),
    (401, 500, 1801, 5000)
]
PB_BREAKPOINTS = [
    (0, 50, 0, 0.5),
    (51, 100, 0.6, 1.0),
    (101, 200, 1.1, 2.0),
    (201, 300, 2.1, 3.0),
    (301, 400, 3.1, 3.5),
    (401, 500, 3.6, 10.0)
]

# --- 2. Sub-Index Calculator ---

def compute_sub_index(Cp, breakpoints):
    """
    Calculates the sub-index for a single pollutant.
    Cp = concentration
    breakpoints = The matching table for that pollutant
    """
    # Find the correct range for the concentration
    for (ILo, IHi, BPLo, BPHi) in breakpoints:
        if BPLo <= Cp <= BPHi:
            # Found the range. Now use the linear interpolation formula
            # Ip = [IHi – ILo / BPHi – BPLo] (Cp – BPLo) + ILo
            Ip = ((IHi - ILo) / (BPHi - BPLo)) * (Cp - BPLo) + ILo
            return round(Ip)
    
    # If concentration is out of the highest range, cap it
    if Cp > breakpoints[-1][3]: # if Cp > max BPHi
        return breakpoints[-1][1] # return max IHi
    # If concentration is below the lowest range (e.g. 0)
    return 0

# --- 3. AQI Category Finder ---

def get_aqi_category(aqi):
    """
    Returns the CPCB category name for a given AQI score.
    """
    if aqi <= 50:
        return "Good"
    elif aqi <= 100:
        return "Satisfactory"
    elif aqi <= 200:
        return "Moderate"
    elif aqi <= 300:
        return "Poor"
    elif aqi <= 400:
        return "Very Poor"
    else:
        return "Severe"

# --- 4. Main AQI Computer ---

def compute_final_aqi(raw_values):
    """
    Takes a dict of raw pollutant values.
    Calculates all sub-indices.
    Returns the final AQI, category, dominant pollutant, and raw values.
    """
    sub_indices = []

    # Calculate sub-index for each pollutant *if* it has a value
    if raw_values.get('pm25') is not None:
        sub_indices.append((compute_sub_index(raw_values['pm25'], PM25_BREAKPOINTS), 'pm25'))
    
    if raw_values.get('pm10') is not None:
        sub_indices.append((compute_sub_index(raw_values['pm10'], PM10_BREAKPOINTS), 'pm10'))
    
    if raw_values.get('co') is not None:
        sub_indices.append((compute_sub_index(raw_values['co'], CO_BREAKPOINTS), 'co'))
        
    if raw_values.get('no2') is not None:
        sub_indices.append((compute_sub_index(raw_values['no2'], NO2_BREAKPOINTS), 'no2'))
        
    if raw_values.get('so2') is not None:
        sub_indices.append((compute_sub_index(raw_values['so2'], SO2_BREAKPOINTS), 'so2'))
        
    if raw_values.get('o3') is not None:
        sub_indices.append((compute_sub_index(raw_values['o3'], O3_BREAKPOINTS), 'o3'))
        
    if raw_values.get('nh3') is not None:
        sub_indices.append((compute_sub_index(raw_values['nh3'], NH3_BREAKPOINTS), 'nh3'))
        
    if raw_values.get('pb') is not None:
        sub_indices.append((compute_sub_index(raw_values['pb'], PB_BREAKPOINTS), 'pb'))
    
    
    # --- THIS IS THE FIX ---
    # We must add the raw values to the dictionary we return.
    
    if not sub_indices:
        # If no data was provided at all
        return {
            'aqi': 0,
            'category': 'No Data',
            'dominant_pollutant': 'N/A',
            # Also add the empty raw values
            'pm25_raw': None, 'pm10_raw': None, 'co_raw': None,
            'no2_raw': None, 'so2_raw': None, 'o3_raw': None,
            'nh3_raw': None, 'pb_raw': None
        }

    # Find the worst (highest) sub-index
    final_aqi, dominant_pollutant = max(sub_indices, key=lambda x: x[0])
    
    # Get the category name
    category = get_aqi_category(final_aqi)
    
    # Return the full result, including the raw values for the chart
    return {
        'aqi': final_aqi,
        'category': category,
        'dominant_pollutant': dominant_pollutant,
        # Add all the original raw values for saving to the DB
        'pm25_raw': raw_values.get('pm25'),
        'pm10_raw': raw_values.get('pm10'),
        'co_raw': raw_values.get('co'),
        'no2_raw': raw_values.get('no2'),
        'so2_raw': raw_values.get('so2'),
        'o3_raw': raw_values.get('o3'),
        'nh3_raw': raw_values.get('nh3'),
        'pb_raw': raw_values.get('pb')
    }