"""Test script for AI microservice functionality."""

import asyncio
from helper_agent import AIServiceClient, check_ai_service


async def test_ai_service():
    """Test the AI service connection and functionality."""
    
    print("🧪 Testing AI Code Helper Service...\n")
    
    # Test 1: Health Check
    print("1️⃣ Testing AI Service Health...")
    is_healthy = await check_ai_service()
    if is_healthy:
        print("   ✅ AI Service is healthy and reachable\n")
    else:
        print("   ❌ AI Service is not available")
        print("   Make sure the AI service is running on port 8001")
        print("   Run: python -m helper_agent.agent_service\n")
        return
    
    # Test 2: Simple Code Analysis
    print("2️⃣ Testing Code Analysis...")
    client = AIServiceClient()
    
    test_code = """
def fibonacci(n):
    if n <= 1:
        return n
    return fibonacci(n-1) + fibonacci(n-2)

result = fibonacci(10)
print(result)
"""
    
    try:
        result = await client.analyze_code(
            code=test_code,
            language="python"
        )
        
        if result['success']:
            print("   ✅ Analysis successful!")
            print(f"   📊 Analysis: {result['analysis']}")
            print(f"   💬 Response preview: {result['response'][:200]}...\n")
        else:
            print(f"   ❌ Analysis failed: {result.get('error')}\n")
    except Exception as e:
        print(f"   ❌ Error: {str(e)}\n")
    
    # Test 3: Specific Query
    print("3️⃣ Testing Specific Query...")
    try:
        result = await client.chat(
            code=test_code,
            query="What's wrong with this implementation and how can I optimize it?"
        )
        
        if result['success']:
            print("   ✅ Query successful!")
            print(f"   💡 AI Response:\n{result['response']}\n")
        else:
            print(f"   ❌ Query failed: {result.get('error')}\n")
    except Exception as e:
        print(f"   ❌ Error: {str(e)}\n")
    
    # Test 4: Bug Detection
    print("4️⃣ Testing Bug Detection...")
    buggy_code = """
def divide_numbers(a, b):
    return a / b

result = divide_numbers(10, 0)
print(result)
"""
    
    try:
        result = await client.analyze_code(
            code=buggy_code,
            query="Are there any bugs or issues in this code?"
        )
        
        if result['success']:
            print("   ✅ Bug detection successful!")
            print(f"   🐛 Analysis: {result['response'][:300]}...\n")
        else:
            print(f"   ❌ Bug detection failed: {result.get('error')}\n")
    except Exception as e:
        print(f"   ❌ Error: {str(e)}\n")
    
    print("=" * 60)
    print("✅ All tests completed!")
    print("=" * 60)


if __name__ == "__main__":
    print("\n" + "=" * 60)
    print("AI CODE HELPER SERVICE - TEST SUITE")
    print("=" * 60 + "\n")
    
    try:
        asyncio.run(test_ai_service())
    except KeyboardInterrupt:
        print("\n\n⚠️  Test interrupted by user")
    except Exception as e:
        print(f"\n\n❌ Test suite error: {str(e)}")
