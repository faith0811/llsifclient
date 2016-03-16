# llsifclient

This is Python 3 package for a partial implementation of the client side APIs of Love Live School Idol Festival (Japanese Android version).

Not all possible client actions are implemented. Some of the things you can do with this package are:

* Registering a new game account
* Importing an existing account using a transfer code
* Logging in to an account, obtaining login bonuses
* Retrieve the stats of an account, like nickname, level, number of Loveca stones, gold, etc.
* Listing contents of present box
* Collecting presents from present box
* Drawing cards (scouting)
* Managing cards

**NOTE: This package is not ready to use out of the box!** The HMAC key that authenticates client messages to the server is not included in the code, so it won't talk to KLab's production servers. See the code for more details.

## API Overview

(This is not a complete documentation of the API. Always read the code, or better yet do a WireShark capture of the actual game client, to understand what's going on.)

LLSIF game clients communicate with the server using fairly standard HTTP, with a bunch of custom headers.

### Client-to-server requests

Client requests for a single action are `POST`ed to `/main.php/module/action`, where `module` and `action` specify the operation. The request body is either empty or a JSON object. Requests for multiple actions in a single request is `POST`ed to `/main.php/api`, with a JSON object in the request body.

Where present, the JSON object may contain some of the following: the `module` and `action` of each action, a timestamp, a "commandNum" (that consists of the account's `login_key`, a timestamp, and a running counter of requests).

### Server-to-client replies

The server always replies with a JSON object in the reply body, possibly gzipped. The root object always contains a `response_data` object, and often contain a `status_code` object. For single action requests, `response_data` directly contain the results. For multiple action requests, `response_data` contains an array.

### Session control

When the game client is launched, it requests an authentication token from the server. All further communications contain this token as well as a running counter (nonce) in the headers. The client then sends a `login_key` and `login_password` to the server. If authenticated successfully, the server issues a fresh auth token and returns the `user_id` associated with the account. The `user_id` is also included in the headers in all future requests.

### Protections against attacks

First, the glaring vulnerability: Since everything runs over HTTP, it's all plaintext, so an attacker in an MITM position can easily intercept `login_key` and `login_password` when a user launches the game client, therefore stealing the account.

Client requests with a body and server responses contain an HTTP header `X-Message-Code`, which is an HMAC-SHA1 computed over the request/response body. This would have stopped 3rd-party clients like this one, but the HMAC key can be found with a bit of patience by disassembling the game client's NDK binary. It can *not* be found by simply running `strings` over the binary; that would be way too easy.

In addition, server replies are signed with a 1024-bit RSA key with the signature in the header `X-Message-Sign`. The public key can be found with `strings`. This does effectively prevent anyone from making private servers that work with the official client.

For client requests that include rhythm game results and scores, there's a "key" in the request body. I have not yet looked into how the key is computed.
