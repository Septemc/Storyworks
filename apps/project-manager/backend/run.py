"""
项目管理应用启动脚本
"""
import uvicorn
import argparse
import sys
from pathlib import Path

# 添加项目根目录到路径
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))


def main():
    parser = argparse.ArgumentParser(description="Storyworks 项目管理应用")
    parser.add_argument("--port", type=int, default=8000, help="服务端口")
    parser.add_argument("--host", type=str, default="127.0.0.1", help="服务地址")
    args = parser.parse_args()

    print(f"启动项目管理应用: http://{args.host}:{args.port}")
    uvicorn.run(
        "app.main:app",
        host=args.host,
        port=args.port,
        reload=True,
        app_dir=str(Path(__file__).parent),
    )


if __name__ == "__main__":
    main()
