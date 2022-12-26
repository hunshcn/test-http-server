# test-http-server

# usage
- /ws
- /file/100m
- /sleep/60
- /sleep/block/60

# dep
pip3 install fastapi "uvicorn[standard]"

# run
python3 -m uvicorn main:app --host 0.0.0.0 --port 5000
