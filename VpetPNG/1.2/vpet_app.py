"""Vpet 桌面程序入口：默认打开托盘启动器；--pet 直接运行桌宠。"""

from __future__ import annotations

import sys


def main() -> None:
    if "--pet" in sys.argv:
        from pet import DesktopPet

        DesktopPet().run()
        return
    from vpet_launcher import main as run_launcher

    run_launcher()


if __name__ == "__main__":
    main()
