# PYTRO API Documentation

Welcome to the detailed documentation for PYTRO-API. This documentation provides additional details, tutorials, and usage examples beyond what's provided in the README.

## API Reference

### Authentication

#### Generate JWT Token

```http
  POST /api/v1/auth/
```

#### Request Body
```json
{
  "secret_key": "string"
}
```

#### Responses
- <span style="color:green;">200 OK - Returns the JWT token</span>
- <span style="color:red;">401 Unauthorized - Returns "Wrong secret key"</span>

#### Get item

```http

```

| Parameter | Type     | Description                       |
| :-------- | :------- | :-------------------------------- |
| `id`      | `string` | **Required**. Id of item to fetch |

#### add(num1, num2)

Takes two numbers and returns the sum.

