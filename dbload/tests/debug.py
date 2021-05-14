import debugpy


print("Starting debugger ...")
debugpy.listen(("localhost", 10001))
print("Waiting for clients to connect 🎉")
debugpy.wait_for_client()
