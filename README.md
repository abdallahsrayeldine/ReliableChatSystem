# Chat App 📨🖥️

Simple GUI chat client using UDP for messages (with sequence numbers + ACKs) and TCP for file transfer. Built with `tkinter` + `ttkthemes`. Runs as *User 1* (there’s a mirror `user2` file for the other client).
Quick, local, and educational — not production-ready. ⚠️

---

## What's here

* UDP messaging with:

  * sequence numbers
  * acknowledgements (`ACK: <seq>`)
  * resend loop for unacknowledged packets
  * duplicate-suppression via `received_messages`
* TCP-based file send/receive (basic)
* `tkinter` GUI (entry, send button, chat box, file dialog)
* Theme: `ttkthemes.ThemedTk("arc")`

---

## Quick start

1. Install dependencies:

```bash
pip install ttkthemes
# tkinter is usually included with Python; if not, install via your OS package manager
```

2. Save the provided script as `user1.py`. Make sure you have the `user2.py` counterpart (mirror ports/addresses).

3. Run both clients on the same machine (two terminals) or on different machines after adjusting host addresses:

```bash
python user1.py   # this file
python user2.py   # other client
```

4. Type a message and press Enter or click **Send**. Use **Send File** to choose and transmit a file.

---

## How it works (protocol summary) 🔁

* **Message format:** `"<seq>:<payload>"` sent over UDP.
* **ACKs:** Receiver sends `ACK: <seq>` back to sender.
* **Resend logic:** `check_acknowledgements()` re-sends unacknowledged messages every 3s.
* **Deduplication:** Received `seq` values are tracked in `received_messages` to avoid duplicate processing.
* **File transfer:** Uses TCP sockets:

  * Sender sends 4 bytes of filename length, then filename, then file bytes.
  * Receiver listens, accepts connection, reads file name length, name, then file content until socket closes.

---

## Ports & bindings (current code)

> Important: the script is using specific localhost ports. Verify both client scripts use complementary ports.

* **User 1 (this file)**

  * UDP bind: `localhost:12346` (listens for incoming UDP)
  * UDP send target: `localhost:12347` (sends messages to peer)
  * TCP file receive: binds `localhost:12341` (server to accept incoming files)
  * TCP file send: connects to `localhost:12349` (target; **NOTE:** this does not match above and is a bug)

* **User 2**

  * Should be set to send to `12346` and bind to `12347` for UDP.
  * For TCP, sender and receiver ports must match (see Known issues below).

---

## Known issues & suggested fixes (read this) ❗

1. **File-transfer port mismatch**

   * Current `send_file()` connects to `12349` while `receive_file()` listens on `12341`. They won't talk.
   * **Fix:** Choose one port for file receive on the peer (e.g., `12341`) and make the other client connect to that same port. Example: change `client_socket.connect(('localhost', 12341))`.

2. **`unacknowledged_messages` stores tuples incorrectly**

   * Code sets: `unacknowledged_messages[seq_num] = seq_num,message` (this stores a `(seq_num, message)` tuple).
   * The resend loop expects `message` to be the payload string and constructs `str(seq) + ':' + str(message)`. That will stringify a tuple — wrong format.
   * **Fix:** Store only the payload (string) or a proper structure, e.g.:

     ```python
     unacknowledged_messages[seq_num] = message_text
     # then resend with:
     sock.sendto(f"{seq}:{message_text}".encode(), peer_addr)
     ```

3. **No timing metadata for resend/backoff**

   * All unacked messages are resent every 3s regardless of how many times — a simple backoff would help.

4. **UDP address hardcoded to localhost**

   * Use variables for host/ports or CLI args to run across different machines.

5. **No graceful shutdown**

   * Threads run forever. Add a shutdown flag and close sockets on exit.

6. **Security & robustness**

   * No authentication, no encryption, no integrity checks (just for local/demo use).

---

## Recommended improvements (short roadmap) ✅

* Fix file port mismatch and tuple bug (see above).
* Add per-message timestamp and exponential backoff for retries.
* Move port/address configuration to CLI args or config file.
* Replace basic resend with ACK timeouts per-message.
* Consider using a reliable UDP library or switch messaging to TCP for guaranteed delivery.
* Add message framing and length prefixes if you move messages to TCP.
* Add UI improvements: message timestamps, message status (sent/acked), error dialogs.

---

## Troubleshooting

* If messages don’t appear:

  * Confirm both clients are bound to complementary UDP ports.
  * Check firewall/antivirus blocking UDP/TCP on those ports.
* If file transfer fails:

  * Verify the receiver’s TCP port and that `send_file()` connects to that same port.
* Use `stderr` logs printed by the script for basic diagnostics (it prints ACK send/resend lines).

---

## Environment

* Python 3.x
* `tkinter` (GUI)
* `ttkthemes` (`pip install ttkthemes`)

---

## Minimal example to fix the two critical bugs

* Make `unacknowledged_messages` map seq → payload string:

```python
unacknowledged_messages[seq_num] = message  # where message = entry_text
```

* Resend using stored payload:

```python
for seq, payload in list(unacknowledged_messages.items()):
    sock.sendto(f"{seq}:{payload}".encode(), ('localhost', 12347))
```

* Make file send connect to the receiver port (e.g., `12341`).

---

## License

Use as you like for learning/demo. No warranty. Be careful if you adapt to production.

---
