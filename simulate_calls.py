#!/usr/bin/env python3
"""
Call Simulation Agents - Generate realistic test data for GoTo Call Automation
Creates 5 different agent types, each simulating specific call scenarios
"""

import requests
import random
from datetime import datetime, timedelta
from typing import List, Dict
import time

API_URL = "http://localhost:8000"

# Realistic data pools
CUSTOMER_NAMES = [
    "Sarah Johnson", "Michael Chen", "Emily Rodriguez", "David Kim", "Jessica Williams",
    "James Brown", "Maria Garcia", "Robert Taylor", "Jennifer Martinez", "Christopher Lee",
    "Amanda Davis", "Daniel Anderson", "Lisa Thompson", "Matthew Wilson", "Karen Moore",
    "Joshua Jackson", "Nicole White", "Andrew Harris", "Rachel Martin", "Kevin Thompson",
    "Samantha Clark", "Brian Lewis", "Michelle Walker", "Ryan Hall", "Laura Allen",
    "Justin Young", "Melissa King", "Brandon Wright", "Stephanie Lopez", "Eric Hill"
]

COMPANY_NUMBERS = [
    "+1 (555) 123-4567", "+1 (555) 987-6543", "+1 (555) 246-8135",
    "+1 (555) 369-2580", "+1 (555) 147-2589"
]

# Agent 1: Customer Support Calls
SUPPORT_SCENARIOS = [
    {
        "topic": "Password Reset",
        "transcript": "Hi, I'm having trouble logging into my account. I've tried resetting my password but I'm not receiving the email. Can you help me with this?",
        "sentiment": "neutral",
        "urgency": 3,
        "action_items": ["Send password reset link manually", "Verify email address in system"],
        "duration_range": (180, 420)
    },
    {
        "topic": "Feature Question",
        "transcript": "Hello! I'm really enjoying your product. I was wondering if there's a way to export my data to Excel? I've looked through the settings but can't find it.",
        "sentiment": "positive",
        "urgency": 2,
        "action_items": ["Send documentation link for data export"],
        "duration_range": (120, 300)
    },
    {
        "topic": "Technical Issue",
        "transcript": "Your app keeps crashing when I try to upload files larger than 10MB. This is really frustrating because I need to share important documents with my team.",
        "sentiment": "negative",
        "urgency": 4,
        "action_items": ["Create support ticket for file upload bug", "Escalate to engineering team", "Follow up within 24 hours"],
        "duration_range": (300, 600)
    },
    {
        "topic": "How-to Question",
        "transcript": "Hi there, I'm new to the platform. Can you walk me through how to set up my first project? I want to make sure I'm doing it correctly.",
        "sentiment": "positive",
        "urgency": 2,
        "action_items": ["Send onboarding guide", "Schedule follow-up call for next week"],
        "duration_range": (240, 480)
    },
    {
        "topic": "Account Issue",
        "transcript": "I've been trying to access my account for the past hour and it keeps saying my credentials are invalid. I know I'm using the right password. What's going on?",
        "sentiment": "negative",
        "urgency": 4,
        "action_items": ["Check account status", "Reset password manually", "Investigate login issues"],
        "duration_range": (200, 400)
    }
]

# Agent 2: Sales Calls
SALES_SCENARIOS = [
    {
        "topic": "Product Demo Request",
        "transcript": "Hi, I saw your product online and I'm very interested! We're a team of 20 and we're looking for a solution exactly like yours. Can we schedule a demo?",
        "sentiment": "positive",
        "urgency": 3,
        "action_items": ["Schedule product demo for next week", "Send pricing information", "Add to sales pipeline"],
        "duration_range": (180, 360)
    },
    {
        "topic": "Upgrade Inquiry",
        "transcript": "We've been using your basic plan for 6 months and we love it! We're ready to upgrade to the professional plan. What's the process?",
        "sentiment": "positive",
        "urgency": 3,
        "action_items": ["Send upgrade options and pricing", "Process upgrade request", "Schedule onboarding call"],
        "duration_range": (150, 300)
    },
    {
        "topic": "Enterprise Interest",
        "transcript": "Hello, I'm calling from a Fortune 500 company and we're evaluating enterprise solutions. We need something that can handle 500+ users. Can you help?",
        "sentiment": "positive",
        "urgency": 5,
        "action_items": ["Schedule enterprise sales call", "Prepare custom proposal", "Connect with enterprise team"],
        "duration_range": (300, 600)
    },
    {
        "topic": "Pricing Question",
        "transcript": "I'm interested in your service but I'm comparing a few options. Can you tell me more about your pricing and what makes you different from competitors?",
        "sentiment": "neutral",
        "urgency": 2,
        "action_items": ["Send detailed pricing breakdown", "Send competitor comparison sheet"],
        "duration_range": (120, 240)
    },
    {
        "topic": "Referral Lead",
        "transcript": "Hi! My colleague recommended your product and said you have amazing customer support. I'd like to learn more about what you offer.",
        "sentiment": "positive",
        "urgency": 3,
        "action_items": ["Send product overview", "Schedule discovery call", "Note referral source"],
        "duration_range": (180, 360)
    }
]

# Agent 3: Billing/Complaint Calls
BILLING_SCENARIOS = [
    {
        "topic": "Billing Error",
        "transcript": "I was charged twice this month! I only have one subscription but my credit card shows two charges. This needs to be fixed immediately.",
        "sentiment": "negative",
        "urgency": 5,
        "action_items": ["Investigate duplicate charge", "Process refund", "Send confirmation email", "Follow up to ensure resolution"],
        "duration_range": (240, 480)
    },
    {
        "topic": "Cancellation Request",
        "transcript": "I want to cancel my subscription. It's too expensive and I'm not using all the features. Can you process this today?",
        "sentiment": "negative",
        "urgency": 3,
        "action_items": ["Process cancellation request", "Send feedback survey", "Offer discount to retain customer"],
        "duration_range": (180, 360)
    },
    {
        "topic": "Invoice Request",
        "transcript": "Hi, I need an invoice for last month's payment. My accounting department needs it for our records. Can you email that to me?",
        "sentiment": "neutral",
        "urgency": 2,
        "action_items": ["Generate and send invoice", "Update billing email preferences"],
        "duration_range": (120, 240)
    },
    {
        "topic": "Payment Failed",
        "transcript": "I received an email saying my payment failed, but my card is definitely active and has funds. What's the problem?",
        "sentiment": "negative",
        "urgency": 4,
        "action_items": ["Check payment processor logs", "Update payment method", "Retry payment manually"],
        "duration_range": (200, 400)
    },
    {
        "topic": "Pricing Complaint",
        "transcript": "Your prices went up 30% without any notice! This is unacceptable. I've been a loyal customer for 2 years and I'm very disappointed.",
        "sentiment": "negative",
        "urgency": 4,
        "action_items": ["Escalate to retention team", "Offer loyalty discount", "Explain pricing change policy"],
        "duration_range": (300, 540)
    }
]

# Agent 4: General Inquiries
GENERAL_SCENARIOS = [
    {
        "topic": "Business Hours",
        "transcript": "Hi, I just wanted to confirm your business hours. Are you open on weekends?",
        "sentiment": "neutral",
        "urgency": 1,
        "action_items": ["Send business hours information"],
        "duration_range": (60, 120)
    },
    {
        "topic": "Integration Question",
        "transcript": "Does your platform integrate with Salesforce? We use it for our CRM and it would be great to have everything connected.",
        "sentiment": "neutral",
        "urgency": 2,
        "action_items": ["Send integration documentation", "Schedule technical call if needed"],
        "duration_range": (120, 240)
    },
    {
        "topic": "Security Inquiry",
        "transcript": "Our IT department wants to know about your security measures. Do you have SOC 2 compliance? What about data encryption?",
        "sentiment": "neutral",
        "urgency": 3,
        "action_items": ["Send security whitepaper", "Connect with IT team", "Schedule security review call"],
        "duration_range": (180, 360)
    },
    {
        "topic": "Feature Request",
        "transcript": "I really like your product! Is there a way to add dark mode? I use the app a lot at night and it would be easier on the eyes.",
        "sentiment": "positive",
        "urgency": 1,
        "action_items": ["Add feature request to product roadmap", "Thank customer for feedback"],
        "duration_range": (90, 180)
    },
    {
        "topic": "Mobile App",
        "transcript": "Do you have a mobile app? I travel a lot and would love to access everything from my phone.",
        "sentiment": "neutral",
        "urgency": 2,
        "action_items": ["Send mobile app download links", "Send mobile app tutorial"],
        "duration_range": (90, 180)
    }
]

# Agent 5: Urgent Issues
URGENT_SCENARIOS = [
    {
        "topic": "Service Outage",
        "transcript": "Your service is completely down! We have a major presentation in 30 minutes and we can't access any of our files. This is a disaster!",
        "sentiment": "negative",
        "urgency": 5,
        "action_items": ["Check service status immediately", "Escalate to ops team", "Provide workaround", "Send hourly updates"],
        "duration_range": (180, 420)
    },
    {
        "topic": "Data Loss",
        "transcript": "All of my project data from the past week is missing! I didn't delete anything. Where did it go? I need this recovered ASAP!",
        "sentiment": "negative",
        "urgency": 5,
        "action_items": ["Initiate data recovery process", "Escalate to engineering", "Provide status updates every hour", "Create incident report"],
        "duration_range": (300, 600)
    },
    {
        "topic": "Security Breach Concern",
        "transcript": "I received a suspicious email claiming to be from your company asking for my password. Is this legitimate? I'm worried my account was compromised.",
        "sentiment": "negative",
        "urgency": 5,
        "action_items": ["Verify account security", "Reset password immediately", "Report phishing attempt", "Enable 2FA", "Send security alert"],
        "duration_range": (240, 480)
    },
    {
        "topic": "Critical Bug",
        "transcript": "There's a bug that's deleting customer orders when we try to export them. We've lost several orders already. This is costing us money!",
        "sentiment": "negative",
        "urgency": 5,
        "action_items": ["Create P0 bug ticket", "Escalate to CTO", "Deploy hotfix", "Recover lost data", "Provide compensation"],
        "duration_range": (360, 720)
    },
    {
        "topic": "Account Lockout",
        "transcript": "I've been locked out of my account for 3 hours and I can't do my work! I've tried everything. I need access right now!",
        "sentiment": "negative",
        "urgency": 5,
        "action_items": ["Unlock account immediately", "Investigate lockout cause", "Provide temporary access", "Follow up to prevent recurrence"],
        "duration_range": (180, 360)
    }
]


class CallSimulatorAgent:
    """Base class for call simulation agents"""

    def __init__(self, agent_name: str, scenarios: List[Dict], call_type: str):
        self.agent_name = agent_name
        self.scenarios = scenarios
        self.call_type = call_type
        self.calls_created = 0

    def generate_phone_number(self) -> str:
        """Generate a random phone number"""
        area_code = random.randint(200, 999)
        exchange = random.randint(200, 999)
        number = random.randint(1000, 9999)
        return f"+1 ({area_code}) {exchange}-{number}"

    def create_call(self, scenario: Dict, caller_name: str) -> Dict:
        """Create a single call with all variables"""
        now = datetime.now()
        # Randomize call time within the past 7 days
        call_time = now - timedelta(
            days=random.randint(0, 7),
            hours=random.randint(0, 23),
            minutes=random.randint(0, 59)
        )

        duration = random.randint(scenario["duration_range"][0], scenario["duration_range"][1])

        # Determine if call is inbound or outbound (80% inbound for realism)
        direction = "inbound" if random.random() < 0.8 else "outbound"

        call_data = {
            "caller_name": caller_name,
            "caller_number": self.generate_phone_number(),
            "called_number": random.choice(COMPANY_NUMBERS),
            "called_name": "Support Team" if direction == "inbound" else caller_name,
            "start_time": call_time.isoformat(),
            "end_time": (call_time + timedelta(seconds=duration)).isoformat(),
            "duration_seconds": duration,
            "direction": direction,
            "status": "completed",
            "recording_url": f"https://recordings.example.com/{random.randint(10000, 99999)}.mp3",
            "transcript": scenario["transcript"],
            "summary": {
                "summary": self._generate_summary(scenario),
                "sentiment": scenario["sentiment"],
                "urgency_score": scenario["urgency"],
                "key_topics": [scenario["topic"]] + self._generate_additional_topics(),
                "action_items": [
                    {
                        "description": action,
                        "priority": scenario["urgency"],
                        "assigned_to": self._assign_to(),
                        "due_date": (now + timedelta(days=random.randint(1, 7))).isoformat()
                    }
                    for action in scenario["action_items"]
                ]
            }
        }

        return call_data

    def _generate_summary(self, scenario: Dict) -> str:
        """Generate AI-like summary"""
        summaries = {
            "positive": [
                f"Customer called regarding {scenario['topic'].lower()}. They expressed satisfaction with the service and requested additional information. Issue was resolved satisfactorily.",
                f"Positive interaction about {scenario['topic'].lower()}. Customer was pleased with the response and asked good questions. Follow-up scheduled.",
                f"Constructive call regarding {scenario['topic'].lower()}. Customer is happy with the product and looking to expand usage."
            ],
            "neutral": [
                f"Customer inquired about {scenario['topic'].lower()}. Standard information provided. No immediate action required.",
                f"Routine call regarding {scenario['topic'].lower()}. Questions answered and documentation shared.",
                f"Customer asked about {scenario['topic'].lower()}. Information provided and call concluded normally."
            ],
            "negative": [
                f"Customer called with concerns about {scenario['topic'].lower()}. They expressed frustration. Issue requires immediate attention.",
                f"Challenging call regarding {scenario['topic'].lower()}. Customer is dissatisfied and needs urgent resolution.",
                f"Escalation needed for {scenario['topic'].lower()}. Customer is upset and situation requires management intervention."
            ]
        }
        return random.choice(summaries[scenario["sentiment"]])

    def _generate_additional_topics(self) -> List[str]:
        """Add random additional topics"""
        all_topics = ["pricing", "features", "support", "billing", "technical", "account", "integration", "security"]
        return random.sample(all_topics, k=random.randint(0, 2))

    def _assign_to(self) -> str:
        """Randomly assign to team members"""
        team = ["John Smith", "Sarah Parker", "Mike Johnson", "Emily Davis", "Chris Lee"]
        return random.choice(team)

    def send_call_to_api(self, call_data: Dict) -> bool:
        """Send call directly to database via API"""
        try:
            # Create call record
            response = requests.post(
                f"{API_URL}/api/calls/simulate",
                json=call_data,
                timeout=10
            )

            if response.status_code in [200, 201]:
                self.calls_created += 1
                return True
            else:
                print(f"❌ Failed to create call: {response.status_code}")
                return False

        except Exception as e:
            print(f"❌ Error sending call: {e}")
            return False

    def run(self, num_calls: int = 5):
        """Run the agent to create multiple calls"""
        print(f"\n{'='*60}")
        print(f"🤖 {self.agent_name} - Starting")
        print(f"📞 Target: {num_calls} {self.call_type} calls")
        print(f"{'='*60}\n")

        for i in range(num_calls):
            scenario = random.choice(self.scenarios)
            caller = random.choice(CUSTOMER_NAMES)

            print(f"  [{i+1}/{num_calls}] Creating call: {caller} - {scenario['topic']}")

            call_data = self.create_call(scenario, caller)
            success = self.send_call_to_api(call_data)

            if success:
                print(f"    ✓ Call created | Sentiment: {scenario['sentiment']} | Urgency: {scenario['urgency']}/5")

            # Small delay to avoid overwhelming the API
            time.sleep(0.5)

        print(f"\n✅ {self.agent_name} completed: {self.calls_created} calls created\n")


def main():
    """Run all 5 agents to simulate dozens of calls"""

    print("\n" + "="*80)
    print(" "*20 + "CALL SIMULATION SYSTEM")
    print(" "*15 + "Generating Realistic Test Data")
    print("="*80)

    # Check if API is available
    try:
        response = requests.get(f"{API_URL}/health", timeout=5)
        if response.status_code != 200:
            print("\n❌ API is not healthy. Please start the backend first.")
            return
    except Exception as e:
        print(f"\n❌ Cannot connect to API at {API_URL}")
        print("   Make sure the backend is running: docker-compose ps")
        return

    # Create 5 different agent types
    agents = [
        CallSimulatorAgent("Agent 1: Customer Support", SUPPORT_SCENARIOS, "support"),
        CallSimulatorAgent("Agent 2: Sales Calls", SALES_SCENARIOS, "sales"),
        CallSimulatorAgent("Agent 3: Billing/Complaints", BILLING_SCENARIOS, "billing"),
        CallSimulatorAgent("Agent 4: General Inquiries", GENERAL_SCENARIOS, "general"),
        CallSimulatorAgent("Agent 5: Urgent Issues", URGENT_SCENARIOS, "urgent")
    ]

    # Each agent creates 6-8 calls (total ~30-40 calls)
    for agent in agents:
        num_calls = random.randint(6, 8)
        agent.run(num_calls)
        time.sleep(1)  # Pause between agents

    total_calls = sum(agent.calls_created for agent in agents)

    print("="*80)
    print(f"✅ SIMULATION COMPLETE")
    print(f"📊 Total calls created: {total_calls}")
    print(f"🌐 View in dashboard: http://localhost:3000")
    print("="*80 + "\n")


if __name__ == "__main__":
    main()
