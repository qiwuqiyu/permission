# ============================================================================
# 冒烟测试 —— 拆包后用来确认「接口路径和响应结构一点没变」
# ----------------------------------------------------------------------------
# 用法（后端必须已经在 127.0.0.1:8000 跑着）：
#   python3.12 scripts/smoke_test.py
# 它只做「建了就得删掉」的临时数据，跑完库里不会留垃圾。
# 以后每次重构/改接口都能再跑一遍，比手动点前端页面快得多。
# ============================================================================
import sys

import httpx

BASE = "http://127.0.0.1:8000"

# 拆包前实际抓到的路径清单，作为对照基准（顺序无关，集合比对）
EXPECTED_PATHS = {
    "/login", "/menus", "/menus/{menu_id}", "/roles",
    "/roles/{role_id}", "/roles/{role_id}/menus", "/users", "/users/{user_id}",
}

passed, failed = 0, 0


def check(name: str, ok: bool, extra: str = "") -> None:
    """打印一行检查结果，顺便计数"""
    global passed, failed
    if ok:
        passed += 1
        print(f"  ✅ {name}")
    else:
        failed += 1
        print(f"  ❌ {name}  {extra}")


def main() -> int:
    client = httpx.Client(base_url=BASE, timeout=5)

    # ---- 1. 接口清单必须和拆包前完全一致 ----
    print("\n【1】路由清单比对")
    paths = set(client.get("/openapi.json").json()["paths"].keys())
    check("路径集合与拆包前一致", paths == EXPECTED_PATHS,
          f"多出={paths - EXPECTED_PATHS} 缺少={EXPECTED_PATHS - paths}")
    check("/docs 可访问", client.get("/docs").status_code == 200)

    # ---- 2. 三个列表接口（读） ----
    print("\n【2】读接口")
    r = client.get("/users")
    check("GET /users 200 且是数组", r.status_code == 200 and isinstance(r.json(), list))
    check("用户项带 role_ids 字段", all("role_ids" in u for u in r.json()) or r.json() == [])

    r = client.get("/menus")
    check("GET /menus 200 且按 sort 升序", r.status_code == 200 and
          [m["sort"] for m in r.json()] == sorted(m["sort"] for m in r.json()))

    r = client.get("/roles")
    check("GET /roles 200 且带 menu_ids/menu_names",
          r.status_code == 200 and all({"menu_ids", "menu_names"} <= set(x) for x in r.json()))

    # ---- 3. 登录（含失败分支） ----
    print("\n【3】登录接口")
    r = client.post("/login", json={"username": "admin", "password": "123456"})
    check("正确密码 -> 200 + token", r.status_code == 200 and "token" in r.json())
    r = client.post("/login", json={"username": "admin", "password": "wrong"})
    check("错误密码 -> 401", r.status_code == 401 and "detail" in r.json())

    # ---- 4. 用户完整生命周期（写） ----
    print("\n【4】用户 CRUD 生命周期")
    r = client.post("/users", json={"username": "123", "password": "x", "email": "a@b.com"})
    check("用户名纯数字 -> 400 且 detail 明确",
          r.status_code == 400 and r.json()["detail"] == "用户名不能是纯数字", r.text)

    r = client.post("/users", json={"username": "smoke_u", "password": "x",
                                    "email": "smoke_u@b.com", "role_ids": [99999]})
    check("不存在的角色 -> 400「角色不存在」（不是 500）",
          r.status_code == 400 and "角色不存在" in r.json().get("detail", ""), r.text)

    r = client.post("/users", json={"username": "smoke_u", "password": "x",
                                    "email": "smoke_u@b.com", "role_ids": [1, 2]})
    created = r.status_code == 200 and r.json()["role_ids"] == [1, 2]
    check("新增用户 200 且回显 role_ids=[1,2]", created, r.text)
    uid = r.json()["id"]

    check("GET /users/{id} 拿得到刚建的", client.get(f"/users/{uid}").json()["username"] == "smoke_u")

    r = client.patch(f"/users/{uid}", json={"email": "smoke_patch@b.com"})
    check("PATCH 只改 email，角色保持 [1,2]",
          r.json()["email"] == "smoke_patch@b.com" and r.json()["role_ids"] == [1, 2], r.text)

    r = client.put(f"/users/{uid}", json={"username": "smoke_u", "password": "y",
                                          "email": "smoke_put@b.com", "role_ids": []})
    check("PUT 传 role_ids=[] 取消全部角色", r.json()["role_ids"] == [], r.text)

    check("DELETE 用户成功", client.delete(f"/users/{uid}").json()["msg"] == "删除成功")
    check("删完再查 -> 404", client.get(f"/users/{uid}").status_code == 404)

    # ---- 5. 菜单生命周期 + 查重 ----
    print("\n【5】菜单接口与校验")
    r = client.post("/menus", json={"name": "冒烟", "path": "no-slash", "sort": 9})
    check("path 不以 / 开头 -> 400",
          r.status_code == 400 and r.json()["detail"] == "路由地址必须以 / 开头")

    r = client.post("/menus", json={"name": "冒烟菜单", "path": "/smoke", "sort": 9})
    check("新增菜单 200", r.status_code == 200, r.text)
    mid = r.json()["id"]

    r = client.post("/menus", json={"name": "冒烟重复", "path": "/smoke", "sort": 9})
    check("重复 path -> 400「该路由地址已存在」",
          r.status_code == 400 and r.json()["detail"] == "该路由地址已存在", r.text)

    r = client.put(f"/menus/{mid}", json={"name": "冒烟菜单改", "path": "/smoke", "sort": 8})
    check("PUT 改成自己的 path 不被误判重复", r.status_code == 200, r.text)

    check("删除菜单成功", client.delete(f"/menus/{mid}").json()["msg"] == "删除成功")

    # ---- 6. 角色 + 菜单授权（两张中间表） ----
    print("\n【6】角色与菜单授权")
    r = client.post("/roles", json={"name": "冒烟角色", "description": "临时"})
    check("新增角色 200", r.status_code == 200, r.text)
    rid = r.json()["id"]

    r = client.post("/roles", json={"name": "冒烟角色", "description": "重复"})
    check("角色名重复 -> 400",
          r.status_code == 400 and r.json()["detail"] == "该角色名已存在")

    r = client.put(f"/roles/{rid}/menus", json={"menu_ids": [1, 2, 99999]})
    check("授权含不存在菜单 -> 400「菜单不存在」",
          r.status_code == 400 and "菜单不存在" in r.json().get("detail", ""), r.text)

    r = client.put(f"/roles/{rid}/menus", json={"menu_ids": [1, 2]})
    check("授权成功且回显 menu_ids/menu_names",
          r.json()["menu_ids"] == [1, 2] and len(r.json()["menu_names"]) == 2, r.text)

    r = client.put(f"/roles/{rid}/menus", json={"menu_ids": [1, 1, 2]})
    check("重复 id 会被去重", r.json()["menu_ids"] == [1, 2], r.text)

    check("删除角色成功", client.delete(f"/roles/{rid}").json()["msg"] == "删除成功")
    check("角色删掉后授权列表里不再出现",
          all(x["id"] != rid for x in client.get("/roles").json()))

    # ---- 7. 数据是否被这次测试污染 ----
    print("\n【7】清理确认（临时数据应已全部删除）")
    check("users 里无 smoke_u",
          all(u["username"] != "smoke_u" for u in client.get("/users").json()))
    check("menus 里无 /smoke",
          all(m["path"] != "/smoke" for m in client.get("/menus").json()))

    print(f"\n{'=' * 46}\n通过 {passed} 项，失败 {failed} 项\n{'=' * 46}")
    return 1 if failed else 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except httpx.ConnectError:
        print(f"连不上 {BASE}，请先启动后端：uvicorn main:app --reload --port 8000")
        sys.exit(2)
