"""Work Queue - Auto-skip already processed issues"""
import requests, json, sys

URL = "http://127.0.0.1:9099"

def get_status(key):
    """Get issue status: new, pending, analyzed, done"""
    try:
        r = requests.post(f"{URL}/recall", json={"key": key}, timeout=3)
        if r.status_code == 200:
            data = r.json()
            value = json.loads(data.get("value", "{}"))
            return value.get("action", "new")
    except:
        pass
    return "new"

def should_skip(key):
    """Check if we should skip this issue (already done or being worked on)"""
    status = get_status(key)
    return status in ["analyzed", "done"]

def add_to_queue(key, data, action="pending"):
    """Add issue to work queue"""
    try:
        # Store the issue data
        requests.post(f"{URL}/store", json={
            "key": key,
            "value": json.dumps({**data, "action": action}),
            "category": "work-queue",
            "tags": json.dumps(["issue", action])
        }, timeout=3)
        
        # Update queue index
        r = requests.post(f"{URL}/recall", json={"key": "index:work-queue"}, timeout=3)
        queue = json.loads(r.json().get("value", "[]")) if r.status_code == 200 else []
        if key not in queue:
            queue.append(key)
        requests.post(f"{URL}/store", json={
            "key": "index:work-queue",
            "value": json.dumps(queue),
            "category": "skill"
        }, timeout=3)
    except Exception as e:
        print(f"[Queue] Error: {e}", file=sys.stderr)

def mark_analyzed(key):
    """Mark issue as analyzed (ready to work)"""
    try:
        r = requests.post(f"{URL}/recall", json={"key": key}, timeout=3)
        if r.status_code == 200:
            value = json.loads(r.json().get("value", "{}"))
            value["action"] = "analyzed"
            requests.post(f"{URL}/store", json={
                "key": key,
                "value": json.dumps(value),
                "category": "work-queue",
                "tags": json.dumps(["issue", "analyzed"])
            }, timeout=3)
    except:
        pass

def mark_done(key):
    """Mark issue as done and remove from pending queue"""
    try:
        # Update issue status
        r = requests.post(f"{URL}/recall", json={"key": key}, timeout=3)
        if r.status_code == 200:
            value = json.loads(r.json().get("value", "{}"))
            value["action"] = "done"
            value["completed"] = "2026-05-11"
            requests.post(f"{URL}/store", json={
                "key": key,
                "value": json.dumps(value),
                "category": "work-queue",
                "tags": json.dumps(["issue", "done"])
            }, timeout=3)
        
        # Remove from pending queue
        r = requests.post(f"{URL}/recall", json={"key": "index:work-queue"}, timeout=3)
        queue = json.loads(r.json().get("value", "[]")) if r.status_code == 200 else []
        if key in queue:
            queue.remove(key)
        requests.post(f"{URL}/store", json={
            "key": "index:work-queue",
            "value": json.dumps(queue)
        }, timeout=3)
    except:
        pass

def list_queue():
    """List all pending issues in work queue"""
    try:
        r = requests.post(f"{URL}/recall", json={"key": "index:work-queue"}, timeout=3)
        queue = json.loads(r.json().get("value", "[]")) if r.status_code == 200 else []
        
        if not queue:
            print("\n📋 Work Queue (empty - all done!)")
            return
        
        print(f"\n📋 Work Queue ({len(queue)} pending):\n")
        for key in queue:
            r2 = requests.post(f"{URL}/recall", json={"key": key}, timeout=3)
            if r2.status_code == 200:
                value = json.loads(r2.json().get("value", "{}"))
                status = value.get("action", "pending")
                emoji = {"pending": "⏳", "analyzed": "🔍", "done": "✅"}.get(status, "❓")
                print(f"  {emoji} #{value.get('number')}: {value.get('title', '')[:45]}")
    except Exception as e:
        print(f"[Queue] Error: {e}")

# CLI
if __name__ == "__main__":
    cmd = sys.argv[1] if len(sys.argv) > 1 else "list"
    if cmd == "list":
        list_queue()
    elif cmd == "done":
        mark_done(sys.argv[2] if len(sys.argv) > 2 else "")
    elif cmd == "analyze":
        mark_analyzed(sys.argv[2] if len(sys.argv) > 2 else "")
    elif cmd == "status":
        print(f"Status: {get_status(sys.argv[2] if len(sys.argv) > 2 else '')}")
