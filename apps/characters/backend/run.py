"""
人物卡应用启动脚本
"""
import uvicorn
import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))


def main():
    parser = argparse.ArgumentParser(description="Storyworks 人物卡应用")
    parser.add_argument("--port", type=int, default=8002, help="服务端口")
    parser.add_argument("--host", type=str, default="127.0.0.1", help="服务地址")
    args = parser.parse_args()

    print(f"启动人物卡应用: http://{args.host}:{args.port}")
    uvicorn.run(
        "app.main:app",
        host=args.host,
        port=args.port,
        reload=True,
        app_dir=str(Path(__file__).parent),
    )


if __name__ == "__main__":
    main()
