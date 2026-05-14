"""Basic import tests to verify all fixes are working."""

import sys
import os

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

# Add app to path
sys.path.insert(0, os.path.dirname(__file__))


def test_app_imports():
    """Test 1: App main module imports without errors."""
    try:
        from app import main
        print("✅ TEST 1 PASSED: App imports successfully")
        return True
    except Exception as e:
        print(f"❌ TEST 1 FAILED: App import error: {e}")
        return False


def test_firebase_service_imports():
    """Test 2: Firebase service imports and initializes gracefully."""
    try:
        from app.services.firebase_service import firebase_service
        print("✅ TEST 2 PASSED: Firebase service imports successfully")
        return True
    except Exception as e:
        print(f"❌ TEST 2 FAILED: Firebase service import error: {e}")
        return False


def test_supabase_service_imports():
    """Test 3: Supabase service imports successfully."""
    try:
        from app.services.supabase_service import supabase_service
        print("✅ TEST 3 PASSED: Supabase service imports successfully")
        return True
    except Exception as e:
        print(f"❌ TEST 3 FAILED: Supabase service import error: {e}")
        return False


def test_all_routes_import():
    """Test 4: All route modules import successfully."""
    try:
        from app.routes.auth import router as auth_router
        from app.routes.chat import router as chat_router
        from app.routes.tasks import router as tasks_router
        from app.routes.whatsapp import router as whatsapp_router
        from app.routes.billing import router as billing_router
        print("✅ TEST 4 PASSED: All routes import successfully")
        return True
    except Exception as e:
        print(f"❌ TEST 4 FAILED: Route import error: {e}")
        return False


def test_fastapi_app_exists():
    """Test 5: FastAPI app object exists and is configured."""
    try:
        from app.main import app
        assert hasattr(app, 'routes'), "App has no routes"
        assert len(app.routes) > 0, "App routes is empty"
        print(f"✅ TEST 5 PASSED: FastAPI app configured with {len(app.routes)} routes")
        return True
    except Exception as e:
        print(f"❌ TEST 5 FAILED: FastAPI app check error: {e}")
        return False


def test_models_import():
    """Test 6: Data models import successfully."""
    try:
        from app.models import (
            ChatMessageRequest,
            Task,
            TaskCreate,
            PersonalizationSettings,
        )
        print("✅ TEST 6 PASSED: All data models import successfully")
        return True
    except Exception as e:
        print(f"❌ TEST 6 FAILED: Models import error: {e}")
        return False


def test_config_loads():
    """Test 7: Configuration loads successfully."""
    try:
        from app.core.config import settings
        assert settings.ENV, "ENV not configured"
        assert settings.SUPABASE_URL, "SUPABASE_URL not configured"
        print("✅ TEST 7 PASSED: Configuration loads successfully")
        return True
    except Exception as e:
        print(f"❌ TEST 7 FAILED: Config load error: {e}")
        return False


def test_no_async_await_mismatch():
    """Test 8: Firebase methods are NOT async (to avoid event loop issues)."""
    try:
        import inspect
        from app.services.firebase_service import firebase_service
        
        # Check that firebase methods are NOT async
        assert not inspect.iscoroutinefunction(firebase_service.verify_id_token), \
            "verify_id_token should NOT be async"
        assert not inspect.iscoroutinefunction(firebase_service.get_user), \
            "get_user should NOT be async"
        assert not inspect.iscoroutinefunction(firebase_service.create_user), \
            "create_user should NOT be async"
        assert not inspect.iscoroutinefunction(firebase_service.update_user), \
            "update_user should NOT be async"
        
        print("✅ TEST 8 PASSED: Firebase methods are synchronous (correct)")
        return True
    except Exception as e:
        print(f"❌ TEST 8 FAILED: Async check error: {e}")
        return False


def test_supabase_methods_are_async():
    """Test 9: Supabase methods ARE async for non-blocking I/O."""
    try:
        import inspect
        from app.services.supabase_service import supabase_service
        
        # Check that supabase methods ARE async
        assert inspect.iscoroutinefunction(supabase_service.get_user_by_firebase_id), \
            "get_user_by_firebase_id should be async"
        assert inspect.iscoroutinefunction(supabase_service.create_message), \
            "create_message should be async"
        assert inspect.iscoroutinefunction(supabase_service.get_tasks), \
            "get_tasks should be async"
        
        print("✅ TEST 9 PASSED: Supabase methods are async (correct)")
        return True
    except Exception as e:
        print(f"❌ TEST 9 FAILED: Async check error: {e}")
        return False


def test_no_import_errors_in_agents():
    """Test 10: Agent module imports without LangChain errors."""
    try:
        from app.agents.base_agents import ChatAgent, WhatsappAgent, GmailAgent, TaskAgent
        print("✅ TEST 10 PASSED: All agents import successfully (no ChatGoogle import error)")
        return True
    except Exception as e:
        print(f"❌ TEST 10 FAILED: Agent import error: {e}")
        return False


def run_all_tests():
    """Run all tests and report results."""
    print("\n" + "=" * 70)
    print("AGENTCOOLIE BACKEND - IMPORT & STRUCTURE TESTS")
    print("=" * 70 + "\n")
    
    tests = [
        test_app_imports,
        test_firebase_service_imports,
        test_supabase_service_imports,
        test_all_routes_import,
        test_fastapi_app_exists,
        test_models_import,
        test_config_loads,
        test_no_async_await_mismatch,
        test_supabase_methods_are_async,
        test_no_import_errors_in_agents,
    ]
    
    results = []
    for test_func in tests:
        try:
            result = test_func()
            results.append(result)
        except Exception as e:
            print(f"❌ Test {test_func.__name__} crashed: {e}")
            results.append(False)
        print()
    
    print("=" * 70)
    passed = sum(results)
    total = len(results)
    print(f"RESULTS: {passed}/{total} tests passed")
    print("=" * 70 + "\n")
    
    if passed == total:
        print("🎉 ALL TESTS PASSED - Backend structure and fixes verified!")
        return 0
    else:
        print(f"⚠️  {total - passed} test(s) failed - see errors above")
        return 1


if __name__ == "__main__":
    exit_code = run_all_tests()
    sys.exit(exit_code)
