import math



# Constants for a simplified drag model
G = 9.81  # m/s^2, gravitational acceleration
R_EARTH = 6371_000  # Earth radius in meters (approx)




#Calculate approximate air density using the International Standard Atmosphere model.
#Parameters:
#   altitude_m: Altitude in meters above sea level
#Returns:
#   Air density in kg/m^3
def air_density(altitude_m):
    # Simplistic: near sea level ~1.225 kg/m^3, decreases with altitude.
    # A rough approximation:
    rho0 = 1.225
    h_scale = 8500  # scale height in meters
    return rho0 * math.exp(-altitude_m / h_scale)





#IMPORTANT:
    #This function takes in weather data at a set aloititude, ideally you would keep getting weather data at each allitude the balloon falls
    # However that would cost too mnay api calls. 
    # So for now we will just use the weather data at the launch site.
#Get wind vector components at a given altitude.
#Parameters:
#   altitude_m: Altitude in meters above sea level
#   weather_data: Weather data structure containing wind information
#Returns:
#   Tuple of (wind_x, wind_y) components in m/s
def wind_vector(altitude_m, weather_data):
    """
    Return (wind_x, wind_y) in m/s, ignoring altitude.
    
    We simply read the wind speed & direction from `weather_data["current"]`
    and convert to an (x, y) vector (east, north) in m/s.

    altitude_m is unused because we only have one wind value.
    """

    
    # Example: reading from "current" data in mph
    wind_speed_mph = weather_data["current"]["wind_speed_10m"]          # e.g. 2.1 mph
    wind_dir_deg   = weather_data["current"]["wind_direction_10m"]      # e.g. 288 degrees FROM north

    # 1) Convert mph to m/s (1 mph ≈ 0.44704 m/s)
    speed_m_s = wind_speed_mph * 0.44704

    # 2) Convert “direction from north, clockwise” to standard math angle
    #    for x=east, y=north coordinate system
    #    θ = 270° − wind_dir_deg
    theta_deg = 270.0 - wind_dir_deg
    theta_rad = math.radians(theta_deg)

    # 3) Decompose into x (east) & y (north)
    wind_x = speed_m_s * math.cos(theta_rad)  # m/s toward east
    wind_y = speed_m_s * math.sin(theta_rad)  # m/s toward north

    return (wind_x, wind_y)





#Calculate drag force acceleration vector acting on an object.
#Parameters:
#   velocity: Tuple of (vx, vy, vz) velocity components in m/s
#   altitude_m: Altitude in meters above sea level
#   cd: Drag coefficient (dimensionless)
#   area: Cross-sectional area in m²
#   mass: Object mass in kg
#Returns:
#   Tuple of (ax, ay, az) acceleration components in m/s²
def drag_force(velocity, altitude_m, cd=1.0, area=0.3, mass=6.80):
    """
    Returns the drag acceleration vector (ax, ay, az) in m/s^2.
    
    velocity = (vx, vy, vz) in m/s
    cd = drag coefficient
    area = cross-sectional area (m^2)
    mass = object mass (kg)
    """
    vx, vy, vz = velocity
    v_mag = math.sqrt(vx*vx + vy*vy + vz*vz)
    
    if v_mag < 1e-6:
        return (0, 0, 0)

    # Air density at current altitude
    rho = air_density(altitude_m)
    # Drag magnitude
    Fd = 0.5 * cd * area * rho * (v_mag**2)
    
    # Drag direction is opposite of velocity
    ax = -Fd * (vx / v_mag) / mass
    ay = -Fd * (vy / v_mag) / mass
    az = -Fd * (vz / v_mag) / mass
    
    return (ax, ay, az)







#Convert geodetic coordinates to Earth-Centered Earth-Fixed (ECEF) coordinates.
#Parameters:
#   lat_deg: Latitude in degrees
#   lon_deg: Longitude in degrees
#   alt_m: Altitude in meters above sea level
#Returns:
#   Tuple of (x, y, z) ECEF coordinates in meters
def latlon_to_xyz(lat_deg, lon_deg, alt_m):

    lat_rad = math.radians(lat_deg)
    lon_rad = math.radians(lon_deg)
    r = R_EARTH + alt_m
    
    x = r * math.cos(lat_rad) * math.cos(lon_rad)
    y = r * math.cos(lat_rad) * math.sin(lon_rad)
    z = r * math.sin(lat_rad)
    return (x, y, z)






#Convert Earth-Centered Earth-Fixed (ECEF) coordinates to geodetic coordinates.
#Parameters:
#   x: ECEF x-coordinate in meters
#   y: ECEF y-coordinate in meters
#   z: ECEF z-coordinate in meters
#Returns:
#   Tuple of (latitude_deg, longitude_deg, altitude_m)
def xyz_to_latlon(x, y, z):

    # Radius from Earth center
    r = math.sqrt(x*x + y*y + z*z)
    
    lat_rad = math.asin(z / r)
    lon_rad = math.atan2(y, x)
    alt_m = r - R_EARTH
    
    lat_deg = math.degrees(lat_rad)
    lon_deg = math.degrees(lon_rad)
    return (lat_deg, lon_deg, alt_m)







def balloon_fall_coords(
    init_lat, init_lon, init_alt_m,
    init_vx=0.0, init_vy=0.0, init_vz=0.0,
    mass=1.0, cd=1.0, area=0.3,
    dt=1.0, weather_data=None, max_time=36000
):
    """
    Numerically simulate the balloon's fall given initial position/velocity.
    - init_lat, init_lon in degrees
    - init_alt_m in meters
    - init_vx, init_vy, init_vz in m/s (optional initial velocity)
    - mass in kg, cd = drag coefficient, area in m^2
    - dt = time step in seconds
    - weather_data: your wind data structure
    - max_time in seconds (safety cap on simulation)
    
    Returns final impact lat/lon, plus maybe a trajectory if desired.
    """

    # Convert lat/lon/alt to ECEF
    x, y, z = latlon_to_xyz(init_lat, init_lon, init_alt_m)
    vx, vy, vz = init_vx, init_vy, init_vz

    time_elapsed = 0.0

    while time_elapsed < max_time:
        # Convert ECEF to lat/lon/alt to find altitude for drag & wind
        lat_deg, lon_deg, alt_m = xyz_to_latlon(x, y, z)

        if alt_m <= 0:
            # We've hit the ground
            return lat_deg, lon_deg

        # 1) Get wind at current altitude (in m/s)
        wind_x, wind_y = (0.0, 0.0)
        if weather_data is not None:
            wind_x, wind_y = wind_vector(alt_m, weather_data)

        # Combine object velocity with wind for relative air velocity
        rel_vx = vx - wind_x
        rel_vy = vy - wind_y
        rel_vz = vz  # wind is usually horizontal, ignoring vertical wind for simplicity

        # 2) Compute drag
        ax_drag, ay_drag, az_drag = drag_force(
            (rel_vx, rel_vy, rel_vz), alt_m, cd=cd, area=area, mass=mass
        )

        # 3) Gravity acceleration (straight down in the local vertical)
        # We'll apply it in the ECEF 'z' direction if we want to be exact, 
        # but simpler is just to do it in the local vertical. 
        # For short distances, local vertical approx is fine:
        ax_gravity = 0.0
        ay_gravity = 0.0
        az_gravity = -G

        # 4) Net acceleration in 'air' frame
        ax = ax_drag + ax_gravity
        ay = ay_drag + ay_gravity
        az = az_drag + az_gravity

        # But note: ax, ay, az are in *local* coordinates if we want to be super accurate.
        # For a simpler approach (small region), we just treat 'up/down' as z.
        # For large distances, you might want to rotate these vectors into ECEF.

        # Let's do a simpler approach: 
        #   We'll assume horizontal plane doesn't rotate much over the fall 
        #   and altitude changes are much more significant. So we'll keep ax, ay in local horizontal.

        # 5) Update velocities
        vx += ax * dt
        vy += ay * dt
        vz += az * dt

        # 6) Update positions in *local* approximation by dx = v*dt
        # But we initially have x,y,z in ECEF. 
        # For a short, approximate approach:
        #   treat (vx, vy) as movement in local horizontal plane (east/north),
        #   treat vz as vertical. Then update lat/lon from that small displacement.
        # 
        # A more rigorous approach: convert local velocity increments to ECEF and then add to (x,y,z).
        # We'll do a rough method:
        d_alt = vz * dt
        new_alt = alt_m + d_alt

        # For horizontal displacement, approximate 1 degree of latitude ~ 111,111 meters,
        #                               1 degree of longitude ~ 111,111 * cos(lat) meters.
        meters_per_deg_lat = 111_111.0
        meters_per_deg_lon = meters_per_deg_lat * math.cos(math.radians(lat_deg))

        # Convert vy -> north-south, vx -> east-west for simplicity
        d_lat = (vy * dt) / meters_per_deg_lat
        d_lon = (vx * dt) / meters_per_deg_lon

        new_lat = lat_deg + math.degrees(d_lat)
        new_lon = lon_deg + math.degrees(d_lon)

        # Now convert back to ECEF for next iteration
        x, y, z = latlon_to_xyz(new_lat, new_lon, new_alt)

        time_elapsed += dt

    # If we exit the loop, it means we never hit alt=0 (maybe something went wrong),
    # or it takes more than 'max_time' seconds to fall.
    lat_deg, lon_deg, _ = xyz_to_latlon(x, y, z)
    
    return lat_deg, lon_deg





