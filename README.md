# Weather Balloon API

This API provides endpoints for tracking weather balloons and predicting their impact locations. The service is deployed on Google Cloud Platform.

## API Base URL

The base URL for the API is:

```
https://balloonapi-943888624435.us-west2.run.app/
```

## API Endpoints

### Get All Weather Balloons Coords

The following endpoint returns all weather balloons coords:

```
GET /coords_all
```

### Get Weather Data

The following endpoint returns weather data for given x, y, z coordinates:

```
GET /weather?x={x}&y={y}&z={z}
```

### Get Impact Location

The following endpoint returns the impact location for a given latitude and longitude:

```
GET /impact?x={x}&y={y}&z={z}
```




## API Documentation

The API documentation is available at:

```
https://balloonapi-943888624435.us-west2.run.app/docs
```
