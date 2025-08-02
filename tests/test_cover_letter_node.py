"""
Tests for CoverLetterNode.

Tests cover letter generation with 5-part structure and narrative integration.
"""

import pytest
from unittest.mock import Mock, patch
from typing import Dict, Any

from nodes import CoverLetterNode


class TestCoverLetterNode:
    """Test suite for CoverLetterNode."""
    
    @pytest.fixture
    def node(self):
        """Create node instance with mocked LLM."""
        with patch('nodes.get_default_llm_wrapper') as mock_get_llm:
            mock_llm = Mock()
            mock_get_llm.return_value = mock_llm
            return CoverLetterNode()
    
    @pytest.fixture
    def narrative_strategy(self):
        """Create sample narrative strategy."""
        return {
            "must_tell_experiences": [
                {
                    "title": "Senior Software Engineer at TechCorp",
                    "reason": "Platform engineering expertise",
                    "key_points": [
                        "Led team of 5 on microservices platform",
                        "Reduced latency by 40%",
                        "Mentored junior engineers"
                    ]
                },
                {
                    "title": "ML Pipeline Project",
                    "reason": "Automation expertise",
                    "key_points": [
                        "Automated ML deployments",
                        "Built scalable infrastructure"
                    ]
                }
            ],
            "differentiators": [
                "Rare combination of optimization and architecture skills",
                "Proven ability to democratize complex technology"
            ],
            "career_arc": {
                "past": "Started as full-stack developer",
                "present": "Leading platform initiatives that enable teams",
                "future": "Ready to architect InnovateTech's next-gen platform"
            },
            "key_messages": [
                "Platform expertise enabling business growth",
                "Leadership combining excellence with empowerment",
                "Track record of on-time delivery with impact"
            ],
            "evidence_stories": [
                {
                    "title": "Microservices Transformation",
                    "challenge": "Monolithic system blocking 50+ developers with daily outages",
                    "action": "Led team to design service mesh platform with GitOps CI/CD",
                    "result": "Delivered early, reduced deploy time to 30min, 3x velocity",
                    "skills_demonstrated": ["Platform Architecture", "Leadership"]
                }
            ]
        }
    
    @pytest.fixture
    def company_research(self):
        """Create sample company research."""
        return {
            "mission": "Democratize AI for every business",
            "culture": ["innovation", "collaboration", "customer-obsessed"],
            "strategic_importance": "Platform role critical for scaling AI products",
            "recent_developments": ["Series C funding", "Expanding engineering team"],
            "team_scope": ["50+ engineers", "distributed globally"],
            "technology_stack_practices": ["Kubernetes", "Python", "GitOps"]
        }
    
    @pytest.fixture
    def suitability_assessment(self):
        """Create sample suitability assessment."""
        return {
            "technical_fit_score": 85,
            "cultural_fit_score": 90,
            "key_strengths": [
                "Platform engineering expertise",
                "Team leadership experience",
                "Cloud architecture skills"
            ],
            "unique_value_proposition": "Rare combination of deep technical skills with proven ability to build platforms that multiply team productivity",
            "overall_recommendation": "Excellent fit for the role"
        }
    
    @pytest.fixture
    def career_db(self):
        """Create minimal career database."""
        return {
            "personal_information": {
                "name": "John Doe",
                "email": "john.doe@email.com",
                "location": "San Francisco, CA"
            }
        }
    
    @pytest.fixture
    def shared_store(self, narrative_strategy, company_research, suitability_assessment, career_db):
        """Create shared store with all required data."""
        return {
            "narrative_strategy": narrative_strategy,
            "company_research": company_research,
            "suitability_assessment": suitability_assessment,
            "requirements": {
                "required_skills": ["Python", "Kubernetes", "Platform Engineering"],
                "preferred_skills": ["Leadership", "ML Infrastructure"]
            },
            "job_title": "Senior Platform Engineer",
            "company_name": "InnovateTech",
            "career_db": career_db
        }
    
    def test_node_initialization(self, node):
        """Test node is initialized correctly."""
        assert node.max_retries == 2
        assert node.wait == 1
        assert hasattr(node, 'llm')
    
    def test_prep_validates_required_data(self, node):
        """Test prep validates required inputs."""
        # Missing narrative strategy
        with pytest.raises(ValueError, match="No narrative strategy"):
            node.prep({"company_research": {}, "suitability_assessment": {"test": "data"}})
        
        # Missing suitability assessment
        with pytest.raises(ValueError, match="No suitability assessment"):
            node.prep({"narrative_strategy": {"test": "data"}, "company_research": {}})
    
    def test_prep_handles_missing_company_research(self, node, shared_store):
        """Test prep creates generic research when missing."""
        del shared_store["company_research"]
        
        with patch('nodes.logger') as mock_logger:
            context = node.prep(shared_store)
            
            # Should warn about missing research
            mock_logger.warning.assert_called_with("No company research available - cover letter will be generic")
            
            # Should have generic research
            assert "company_research" in context
            assert context["company_research"]["mission"] == "To be a leader in the industry"
    
    def test_prep_extracts_all_context(self, node, shared_store):
        """Test prep extracts all required context."""
        context = node.prep(shared_store)
        
        assert "narrative_strategy" in context
        assert "company_research" in context
        assert "suitability_assessment" in context
        assert "requirements" in context
        assert "job_title" in context
        assert "company_name" in context
        assert "career_db" in context
    
    def test_exec_generates_cover_letter(self, node, shared_store):
        """Test exec generates cover letter with 5-part structure."""
        context = node.prep(shared_store)
        
        # Mock LLM response
        mock_letter = """Dear Hiring Manager,

As InnovateTech works to democratize AI for every business, I recognize the critical need for a robust platform that can scale your AI products globally. My experience leading platform initiatives that enable engineering teams aligns perfectly with this challenge. I'm writing to express my strong interest in the Senior Platform Engineer role, where my platform expertise can directly enable your business growth.

I offer a rare combination of deep technical skills with proven ability to build platforms that multiply team productivity. In my recent role as Senior Software Engineer at TechCorp, I led a team of 5 engineers to deliver a microservices platform that reduced API latency by 40% and now serves over 100 services. This experience directly demonstrates the platform engineering expertise you're seeking.

Throughout my career, I've consistently delivered complex systems on time with measurable impact. When faced with a monolithic system blocking 50+ developers with daily outages, I led the team to design a service mesh platform with GitOps CI/CD. We delivered the platform two weeks early, reduced deployment time from days to 30 minutes, and enabled 3x faster feature velocity. This transformation showcases my ability to solve exactly the kinds of platform challenges InnovateTech faces.

I'm particularly drawn to InnovateTech's innovation-driven culture and customer-obsessed approach. Your recent Series C funding and engineering team expansion signal an exciting growth phase where my platform expertise would be especially valuable. My vision is to architect InnovateTech's next-generation platform that not only scales your AI products but also empowers your engineering teams to innovate faster. My unique combination of optimization and architecture skills would bring valuable perspective to your platform strategy.

I am confident that my platform expertise enabling business growth, leadership combining excellence with empowerment, and track record of on-time delivery with impact make me an ideal candidate for this role. I would welcome the opportunity to discuss how I can contribute to InnovateTech's mission of democratizing AI for every business.

Thank you for your consideration. I look forward to speaking with you soon.

Sincerely,
John Doe"""
        
        node.llm.call_llm_sync.return_value = mock_letter
        
        result = node.exec(context)
        
        # Verify LLM was called
        node.llm.call_llm_sync.assert_called_once()
        
        # Verify result
        assert "Dear Hiring Manager" in result
        assert "InnovateTech" in result
        assert "Senior Platform Engineer" in result
        assert "John Doe" in result
    
    def test_prompt_includes_narrative_elements(self, node, shared_store):
        """Test prompt includes all narrative strategy elements."""
        context = node.prep(shared_store)
        prompt = node._build_cover_letter_prompt(context)
        
        # Career arc
        assert "Leading platform initiatives that enable teams" in prompt  # Present
        assert "Ready to architect InnovateTech's next-gen platform" in prompt  # Future
        
        # Key messages
        assert "Platform expertise enabling business growth" in prompt
        
        # Differentiators
        assert "Rare combination of optimization and architecture skills" in prompt
        
        # Evidence stories
        assert "Microservices Transformation" in prompt
        assert "Monolithic system blocking 50+ developers" in prompt
    
    def test_prompt_includes_company_research(self, node, shared_store):
        """Test prompt includes company research elements."""
        context = node.prep(shared_store)
        prompt = node._build_cover_letter_prompt(context)
        
        # Company elements
        assert "Democratize AI for every business" in prompt  # Mission
        assert "innovation, collaboration, customer-obsessed" in prompt  # Culture
        assert "Platform role critical for scaling AI products" in prompt  # Strategic importance
        assert "Series C funding" in prompt  # Recent developments
    
    def test_prompt_includes_suitability_assessment(self, node, shared_store):
        """Test prompt includes suitability assessment."""
        context = node.prep(shared_store)
        prompt = node._build_cover_letter_prompt(context)
        
        # Assessment elements
        assert "Rare combination of deep technical skills" in prompt  # UVP
        assert "Technical Fit: 85/100" in prompt
        assert "Cultural Fit: 90/100" in prompt
        assert "Platform engineering expertise" in prompt  # Key strength
    
    def test_prompt_structure_instructions(self, node, shared_store):
        """Test prompt includes 5-part structure instructions."""
        context = node.prep(shared_store)
        prompt = node._build_cover_letter_prompt(context)
        
        # All 5 parts
        assert "1. HOOK" in prompt
        assert "2. VALUE PROPOSITION" in prompt
        assert "3. EVIDENCE" in prompt
        assert "4. COMPANY FIT" in prompt
        assert "5. CALL TO ACTION" in prompt
        
        # Specific instructions
        assert "Start with company's current need/goal" in prompt
        assert "State your unique value" in prompt
        assert "Tell a CAR story" in prompt
        assert "Reference specific aspect of company culture" in prompt
        assert "Reinforce all 3 key messages" in prompt
    
    def test_validate_structure(self, node):
        """Test structure validation logic."""
        # Valid letter
        valid_letter = """Dear Hiring Manager,

Paragraph 1 - Hook

Paragraph 2 - Value Prop

Paragraph 3 - Evidence

Paragraph 4 - Company Fit

Paragraph 5 - Call to Action

Sincerely,
Name"""
        
        assert node._validate_structure(valid_letter) is True
        
        # Too few paragraphs
        short_letter = """Dear Hiring Manager,

Only two paragraphs here.

Sincerely,
Name"""
        
        assert node._validate_structure(short_letter) is False
        
        # Missing greeting
        no_greeting = """First paragraph

Second paragraph

Third paragraph

Fourth paragraph

Fifth paragraph

Sincerely,
Name"""
        
        assert node._validate_structure(no_greeting) is False
    
    def test_fallback_cover_letter(self, node, shared_store):
        """Test fallback cover letter generation."""
        context = node.prep(shared_store)
        
        # Mock LLM failure
        node.llm.call_llm_sync.side_effect = Exception("LLM error")
        
        result = node.exec(context)
        
        # Should have all key elements
        assert "Dear Hiring Manager" in result
        assert "Senior Platform Engineer" in result
        assert "InnovateTech" in result
        
        # Should include narrative elements
        assert "Leading platform initiatives that enable teams" in result  # Present
        assert "Platform expertise enabling business growth" in result  # Key message
        assert "Rare combination of deep technical skills" in result  # UVP
        
        # Should have proper structure
        assert "Sincerely,\nJohn Doe" in result
    
    def test_short_letter_triggers_fallback(self, node, shared_store):
        """Test short response triggers fallback."""
        context = node.prep(shared_store)
        
        # Mock very short response
        node.llm.call_llm_sync.return_value = "Too short"
        
        result = node.exec(context)
        
        # Should use fallback
        assert len(result) > 300
        assert "Dear Hiring Manager" in result
    
    def test_invalid_structure_triggers_fallback(self, node, shared_store):
        """Test invalid structure triggers fallback."""
        context = node.prep(shared_store)
        
        # Mock response with too few paragraphs
        node.llm.call_llm_sync.return_value = """Dear Manager,

Only two paragraphs.

Sincerely,
John"""
        
        result = node.exec(context)
        
        # Should use fallback (which has proper structure)
        paragraphs = [p for p in result.split('\n\n') if p.strip()]
        assert len(paragraphs) >= 5
    
    def test_post_stores_cover_letter(self, node, shared_store):
        """Test post stores cover letter in shared store."""
        cover_letter = """Dear Hiring Manager,

Test cover letter content.

Multiple paragraphs here.

More content.

Final paragraph.

Sincerely,
John Doe"""
        
        # Clear any existing letter
        if "cover_letter_text" in shared_store:
            del shared_store["cover_letter_text"]
        
        action = node.post(shared_store, {}, cover_letter)
        
        assert action == "cover_letter_generated"
        assert "cover_letter_text" in shared_store
        assert shared_store["cover_letter_text"] == cover_letter
    
    def test_post_logging(self, node, shared_store):
        """Test post logs cover letter summary."""
        cover_letter = """Dear Hiring Manager,

I am writing about the Senior Platform Engineer role at InnovateTech.

More content here.

I look forward to discussing this opportunity.

Sincerely,
John Doe"""
        
        with patch('nodes.logger') as mock_logger:
            node.post(shared_store, {}, cover_letter)
            
            # Should log word count and paragraphs
            calls = [call[0][0] for call in mock_logger.info.call_args_list]
            assert any("words" in call for call in calls)
            assert any("paragraphs" in call for call in calls)
            
            # Should log element presence
            assert any("Cover letter elements:" in call for call in calls)
    
    def test_format_evidence_stories(self, node):
        """Test evidence story formatting."""
        # With evidence stories
        stories = [
            {
                "title": "Platform Transformation",
                "challenge": "Legacy system causing daily outages and blocking development teams from deploying efficiently"
            },
            {
                "title": "ML Pipeline",
                "challenge": "Manual ML deployment taking days"
            }
        ]
        
        formatted = node._format_evidence_stories(stories, [])
        assert "Platform Transformation" in formatted
        assert "Legacy system causing daily outages" in formatted
        assert "ML Pipeline" in formatted
        
        # Without stories but with must-tells
        must_tells = [
            {
                "title": "Senior Engineer Role",
                "key_points": ["Led platform team", "Improved performance"]
            }
        ]
        
        formatted = node._format_evidence_stories([], must_tells)
        assert "Senior Engineer Role" in formatted
        assert "Led platform team" in formatted
        
        # Neither stories nor must-tells
        formatted = node._format_evidence_stories([], [])
        assert "Draw from career database" in formatted
    
    def test_format_company_research(self, node):
        """Test company research formatting."""
        research = {
            "mission": "To revolutionize how businesses use AI and make it accessible to everyone",
            "culture": ["innovation", "transparency", "customer-first"],
            "strategic_importance": "This platform role is critical for scaling our infrastructure",
            "recent_developments": ["$50M Series C", "Launching in Europe"]
        }
        
        formatted = node._format_company_research(research)
        
        assert "Mission: To revolutionize" in formatted
        assert "Culture: innovation, transparency, customer-first" in formatted
        assert "Role Importance: This platform role" in formatted
        assert "Recent: $50M Series C, Launching in Europe" in formatted
    
    def test_handles_missing_career_db_info(self, node, shared_store):
        """Test handling of missing personal information."""
        # Remove personal info
        del shared_store["career_db"]["personal_information"]
        
        context = node.prep(shared_store)
        
        # Fallback should handle missing name
        fallback = node._create_fallback_cover_letter(context)
        assert "Your Name" in fallback
    
    def test_handles_empty_narrative_sections(self, node, shared_store):
        """Test handling of empty narrative sections."""
        # Empty various sections
        shared_store["narrative_strategy"]["evidence_stories"] = []
        shared_store["narrative_strategy"]["differentiators"] = []
        
        context = node.prep(shared_store)
        
        # Should handle gracefully
        prompt = node._build_cover_letter_prompt(context)
        assert "Evidence Stories Available" in prompt
        
        # Fallback should work
        fallback = node._create_fallback_cover_letter(context)
        assert len(fallback) > 500  # Reasonable length
    
    def test_key_messages_indexing(self, node, shared_store):
        """Test safe indexing of key messages."""
        # Only 2 key messages instead of 3
        shared_store["narrative_strategy"]["key_messages"] = [
            "Message 1",
            "Message 2"
        ]
        
        context = node.prep(shared_store)
        
        # Should not crash
        fallback = node._create_fallback_cover_letter(context)
        assert "Message 1" in fallback
        assert "Message 2" in fallback