#!/usr/bin/env python3
"""
FACBT Test Script - Test the Facebook Account Creator Bot functionality
"""

import asyncio
import sys
import os
import json
from pathlib import Path

# Add the current directory to Python path
sys.path.insert(0, str(Path(__file__).parent))

from core.engine import FACBTEngine
from utils.config_manager import ConfigurationManager
from utils.logger import LoggerFactory


async def test_bot_components():
    """Test individual bot components"""
    print("🧪 Testing FACBT Components...")
    
    try:
        # Initialize configuration
        config_manager = ConfigurationManager()
        config = config_manager.get_configuration()
        
        # Initialize logger
        logger = LoggerFactory.create_logger("test_bot")
        logger.info("Starting FACBT component tests...")
        
        # Initialize engine
        engine = FACBTEngine(config)
        await engine.initialize()
        
        # Test proxy manager
        print("\n📡 Testing Proxy Manager...")
        proxy_stats = await engine.proxy_manager.get_statistics()
        print(f"   ✅ Working proxies: {proxy_stats['working_proxies']}")
        print(f"   ✅ Success rate: {proxy_stats['success_rate']:.1f}%")
        
        # Test user agent manager
        print("\n🕵️ Testing User Agent Manager...")
        ua_stats = await engine.user_agent_manager.get_statistics()
        print(f"   ✅ Total user agents: {ua_stats['total_user_agents']}")
        print(f"   ✅ Browser distribution: {ua_stats['browser_distribution']}")
        
        # Test email manager
        print("\n📧 Testing Email Manager...")
        email_stats = await engine.email_manager.get_statistics()
        print(f"   ✅ Available services: {email_stats['available_services']}")
        print(f"   ✅ Custom emails: {email_stats['custom_emails_count']}")
        
        # Test identity manager
        print("\n👤 Testing Identity Manager...")
        test_identity = await engine.identity_manager.generate_identity()
        print(f"   ✅ Generated identity: {test_identity.first_name} {test_identity.last_name}")
        print(f"   ✅ Country: {test_identity.country}")
        print(f"   ✅ Age: {test_identity.age}")
        
        # Test behavior simulator
        print("\n🤖 Testing Human Behavior Simulator...")
        behavior_stats = engine.behavior_simulator.get_current_behavior_stats()
        print(f"   ✅ Profile type: {behavior_stats['profile_type']}")
        print(f"   ✅ Typing WPM: {behavior_stats['typing_wpm']}")
        print(f"   ✅ Mouse speed: {behavior_stats['mouse_speed']}")
        
        # Test anti-detection system
        print("\n🛡️ Testing Anti-Detection System...")
        detection_report = await engine.anti_detection.get_detection_report()
        print(f"   ✅ Stealth mode: {detection_report['stealth_mode']}")
        print(f"   ✅ Fingerprint randomization: {detection_report['fingerprint_randomization']}")
        print(f"   ✅ Rate limiting: {detection_report['rate_limiting_active']}")
        
        print("\n✅ All component tests passed!")
        return True
        
    except Exception as e:
        print(f"\n❌ Component test failed: {e}")
        return False


async def test_account_creation_dry_run():
    """Test account creation process (dry run without actual submission)"""
    print("\n🎯 Testing Account Creation Process (Dry Run)...")
    
    try:
        # Initialize configuration
        config_manager = ConfigurationManager()
        config = config_manager.get_configuration()
        
        # Set test mode
        config['engine']['test_mode'] = True
        config['browser']['headless'] = True
        
        # Initialize engine
        engine = FACBTEngine(config)
        await engine.initialize()
        
        # Generate test identity
        identity = await engine.identity_manager.generate_identity()
        print(f"   📝 Test identity: {identity.first_name} {identity.last_name}")
        print(f"   📧 Email will be: {identity.email or 'auto-generated'}")
        print(f"   🌍 Country: {identity.country}")
        
        # Test resource allocation
        proxy = await engine.proxy_manager.get_proxy()
        user_agent = await engine.user_agent_manager.get_user_agent()
        
        if proxy:
            print(f"   🌐 Proxy: {proxy.host}:{proxy.port} ({proxy.country or 'Unknown'})")
        else:
            print("   ⚠️ No proxy available")
            
        print(f"   🕵️ User Agent: {user_agent.browser.value} {user_agent.browser_version}")
        
        # Test behavior simulation
        typing_actions = await engine.behavior_simulator.simulate_typing("Test Name")
        print(f"   ⌨️ Typing simulation: {len(typing_actions)} actions generated")
        
        # Test anti-detection
        fingerprint = await engine.anti_detection.bypass_javascript_detection()
        print(f"   🛡️ Browser fingerprint generated: {len(fingerprint)} properties")
        
        print("   ✅ Account creation dry run completed successfully!")
        return True
        
    except Exception as e:
        print(f"   ❌ Account creation test failed: {e}")
        return False


async def test_custom_email_functionality():
    """Test custom email functionality"""
    print("\n📧 Testing Custom Email Functionality...")
    
    try:
        # Initialize configuration
        config_manager = ConfigurationManager()
        config = config_manager.get_configuration()
        
        # Initialize engine
        engine = FACBTEngine(config)
        await engine.initialize()
        
        # Test adding custom email
        test_email = "test@example.com"
        result = await engine.email_manager.add_custom_email(test_email)
        print(f"   ✅ Added custom email: {result}")
        
        # Test listing custom emails
        custom_emails = await engine.email_manager.list_custom_emails()
        print(f"   ✅ Custom emails: {custom_emails}")
        
        # Test setting verification code
        await engine.email_manager.set_verification_code(test_email, "123456")
        print(f"   ✅ Set verification code for {test_email}")
        
        # Test getting verification code
        code = await engine.email_manager.get_verification_code(test_email)
        print(f"   ✅ Retrieved verification code: {code}")
        
        print("   ✅ Custom email functionality test passed!")
        return True
        
    except Exception as e:
        print(f"   ❌ Custom email test failed: {e}")
        return False


async def main():
    """Main test function"""
    print("🚀 FACBT (Facebook Account Creator Bot) Test Suite")
    print("=" * 60)
    
    # Test results
    results = []
    
    # Run component tests
    results.append(await test_bot_components())
    
    # Run account creation dry run
    results.append(await test_account_creation_dry_run())
    
    # Run custom email tests
    results.append(await test_custom_email_functionality())
    
    # Summary
    print("\n" + "=" * 60)
    print("📊 Test Summary:")
    print(f"   ✅ Passed: {sum(results)}")
    print(f"   ❌ Failed: {len(results) - sum(results)}")
    
    if all(results):
        print("\n🎉 All tests passed! FACBT is ready to use.")
        print("\n📋 Usage Instructions:")
        print("   1. Run: python3 main.py")
        print("   2. Choose your options from the menu")
        print("   3. For custom emails, use the 'Custom Email' option")
        print("   4. Monitor the logs for progress")
        
        return 0
    else:
        print("\n⚠️ Some tests failed. Please check the configuration and dependencies.")
        return 1


if __name__ == "__main__":
    try:
        exit_code = asyncio.run(main())
        sys.exit(exit_code)
    except KeyboardInterrupt:
        print("\n\n⏹️ Tests interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n\n💥 Test suite crashed: {e}")
        sys.exit(1)

