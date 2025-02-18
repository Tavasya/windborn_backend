# Weather Balloon API

This API provides endpoints for tracking weather balloons and predicting their impact locations. The service is deployed on Google Cloud Platform.

## API Base URL

The base URL for the API is:

```
https://weather-balloon-api.uc.r.appspot.com/
```

## API Endpoints

### Get Weather Data

The following endpoint returns weather data for a given latitude and longitude:

```
GET /weather?lat={latitude}&lon={longitude}
```

### Get Impact Location

The following endpoint returns the impact location for a given latitude and longitude:

```
GET /impact?lat={latitude}&lon={longitude}
```



## Deployment

The API is deployed on Google Cloud Platform using the following command:

```
gcloud app deploy
```

## API Documentation

The API documentation is available at:

```
https://weather-balloon-api.uc.r.appspot.com/docs
```
