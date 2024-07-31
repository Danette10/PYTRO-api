Welcome to the detailed documentation for PYTRO-API. This documentation provides additional details, tutorials, and usage examples beyond what's provided in the README.

## API Reference

## Table of Contents

- [Authentication](#authentication)
- [Command Operations](#command-operations)
- [Client Operations](#client-operations)
- [Screenshot Operations](#screenshot-operations)
- [Microphone Operations](#microphone-operations)
- [Browser Data Operations](#browser-data-operations)
- [Keylogger Operations](#keylogger-operations)
- [Clipboard Operations](#clipboard-operations)
- [Webcam Operations](#webcam-operations)
- [Directory Operations](#directory-operations)
- [Download File Operations](#download-file-operations)

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

### Command Operations

#### Send a Command to a Client
```http
POST /api/v1/command/{client_id}
```

#### Request Parameters

| Parameter | Type     | Description                       |
| :-------- | :------- | :-------------------------------- |
| `client_id`      | `int` | **Required**. ID of the client |

#### Request Body

```json
{
  "command": "string",
  "params": "object"
}
```

### Client Operations
```http
GET /api/v1/clients/
```

#### Query Parameters
| Parameter | Type     | Description                       |
| :-------- | :------- | :-------------------------------- |
| `status`      | `str` | Filter clients by their status (online/offline) |

### Screenshot Operations

#### Get Screenshots by Client ID
```http
GET /api/v1/screenshot/client/{client_id}
```

#### Request Parameters
| Parameter | Type     | Description                       |
| :-------- | :------- | :-------------------------------- |
| `client_id`      | `int` | **Required**. ID of the client |

#### Get Screenshot Image
```http
GET /api/v1/screenshot/image/{screenshot_id}
```

#### Request Parameters
| Parameter | Type     | Description                       |
| :-------- | :------- | :-------------------------------- |
| `screenshot_id`      | `int` | **Required**. ID of the screenshot |

### Microphone Operations

#### Get Microphone Recordings by Client ID
```http
GET /api/v1/microphone/client/{client_id}
```

#### Request Parameters
| Parameter | Type     | Description                       |
| :-------- | :------- | :-------------------------------- |
| `client_id`      | `int` | **Required**. ID of the client |

#### Get Microphone Recording
```http
GET /api/v1/microphone/audio/{microphone_id}
```

#### Request Parameters
| Parameter | Type     | Description                       |
| :-------- | :------- | :-------------------------------- |
| `microphone_id`      | `int` | **Required**. ID of the microphone recording |

### Browser Data Operations

#### Get Browser Data by Client ID
```http
GET /api/v1/browser/client/{client_id}/{browser_name}
```

#### Request Parameters
| Parameter | Type     | Description                       |
| :-------- | :------- | :-------------------------------- |
| `client_id`      | `int` | **Required**. ID of the client |
| `browser_name`      | `string` | **Required**. Name of the browser |

#### Get Browser Data File
```http
GET /api/v1/browser/data/{browser_id}
```

#### Request Parameters
| Parameter | Type     | Description                       |
| :-------- | :------- | :-------------------------------- |
| `browser_id`      | `int` | **Required**. ID of the browser data |

### Keylogger Operations

#### Get Keyloggers by Client ID
```http
GET /api/v1/keylogger/client/{client_id}
```

#### Request Parameters
| Parameter | Type     | Description                       |
| :-------- | :------- | :-------------------------------- |
| `client_id`      | `int` | **Required**. ID of the client |

#### Get Keylogger Log
```http
GET /api/v1/keylogger/log/{keylogger_id}
```

#### Request Parameters
| Parameter | Type     | Description                       |
| :-------- | :------- | :-------------------------------- |
| `keylogger_id`      | `int` | **Required**. ID of the keylogger log |

### Clipboard Operations

#### Get Clipboard Data by Client ID
```http
GET /api/v1/clipboard/client/{client_id}
```

#### Request Parameters
| Parameter | Type     | Description                       |
| :-------- | :------- | :-------------------------------- |
| `client_id`      | `int` | **Required**. ID of the client |

#### Get Clipboard File
```http
GET /api/v1/clipboard/content/{clipboard_id}
```

#### Request Parameters
| Parameter | Type     | Description                       |
| :-------- | :------- | :-------------------------------- |
| `clipboard_id`      | `int` | **Required**. ID of the clipboard data |

### Webcam Operations

#### Get Webcam Link
```http
GET /api/v1/webcam/link/{client_id}
```

#### Request Parameters
| Parameter | Type     | Description                       |
| :-------- | :------- | :-------------------------------- |
| `client_id`      | `int` | **Required**. ID of the client |

#### Stop Webcam
```http
GET /api/v1/webcam/stop/{client_id}
```

#### Request Parameters
| Parameter | Type     | Description                       |
| :-------- | :------- | :-------------------------------- |
| `client_id`      | `int` | **Required**. ID of the client |

#### Stream Webcam
```http
GET /api/v1/webcam/{client_id}
```

#### Request Parameters
| Parameter | Type     | Description                       |
| :-------- | :------- | :-------------------------------- |
| `client_id`      | `int` | **Required**. ID of the client |

### Directory Operations

#### List Directory
```http
POST /api/v1/directory/client/{client_id}
```

#### Request Parameters
| Parameter | Type     | Description                       |
| :-------- | :------- | :-------------------------------- |
| `client_id`      | `int` | **Required**. ID of the client |

#### Request Body
```json
{
  "dir_path": "string",
  "user_id": "int"
}
```

### Download File Operations

#### List Downloaded Files by Client ID
```http
GET /api/v1/download/client/{client_id}
```

#### Request Parameters
| Parameter | Type     | Description                       |
| :-------- | :------- | :-------------------------------- |
| `client_id`      | `int` | **Required**. ID of the client |

#### Get Downloaded File
```http
GET /api/v1/download/file/{download_file_id}
```

#### Request Parameters
| Parameter | Type     | Description                       |
| :-------- | :------- | :-------------------------------- |
| `download_file_id`      | `int` | **Required**. ID of the downloaded file |
