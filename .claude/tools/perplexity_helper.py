#!/usr/bin/env python3
"""
Perplexity AI Helper - Deep Research with Real-Time Web Search

Perplexity AI provides:
- Real-time web search and analysis
- Citations and sources for all claims
- Deep research capabilities
- Multiple model options for different use cases
"""

import os
import sys
import json
import argparse
import requests
from typing import Optional, Dict, Any, List
from datetime import datetime


class PerplexityClient:
    """Client for Perplexity AI API"""

    def __init__(self, api_key: Optional[str] = None, model: Optional[str] = None):
        """
        Initialize Perplexity client

        Args:
            api_key: Perplexity API key (or use PERPLEXITY_API_KEY env var)
            model: Model to use (default: llama-3.1-sonar-large-128k-online)
        """
        self.api_key = api_key or os.getenv('PERPLEXITY_API_KEY')
        if not self.api_key:
            raise ValueError(
                "API key is required. Set PERPLEXITY_API_KEY env variable or pass api_key parameter"
            )

        # Use correct Perplexity model name
        # Common models: sonar, sonar-pro, sonar-reasoning
        self.model = model or os.getenv('PERPLEXITY_MODEL', 'sonar')
        self.base_url = "https://api.perplexity.ai"
        self.headers = {
            "accept": "application/json",
            "content-type": "application/json",
            "authorization": f"Bearer {self.api_key}"
        }

    def research(
        self,
        query: str,
        system_prompt: Optional[str] = None,
        temperature: float = 0.2,
        max_tokens: int = 4000,
        return_citations: bool = True,
        return_images: bool = False
    ) -> Dict[str, Any]:
        """
        Perform deep research query

        Args:
            query: Research question or topic
            system_prompt: Optional system instructions
            temperature: Sampling temperature (0-2, lower = more focused)
            max_tokens: Maximum tokens in response
            return_citations: Include source citations
            return_images: Include relevant images

        Returns:
            Dict with response, citations, and metadata

        Example:
            >>> client = PerplexityClient()
            >>> result = client.research(
            ...     query="What are the latest developments in AI agents for 2025?",
            ...     return_citations=True
            ... )
            >>> print(result['content'])
            >>> for citation in result['citations']:
            ...     print(f"Source: {citation}")
        """
        messages = []

        # Add system prompt if provided
        if system_prompt:
            messages.append({
                "role": "system",
                "content": system_prompt
            })

        # Add user query
        messages.append({
            "role": "user",
            "content": query
        })

        payload = {
            "model": self.model,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens
        }

        # Add optional parameters only if True
        if return_citations:
            payload["return_citations"] = True
        if return_images:
            payload["return_images"] = True

        try:
            response = requests.post(
                f"{self.base_url}/chat/completions",
                headers=self.headers,
                json=payload,
                timeout=120
            )

            # Check for errors
            if response.status_code != 200:
                error_detail = response.text
                raise Exception(f"API returned {response.status_code}: {error_detail}")

            data = response.json()

            # Extract response and citations
            choice = data['choices'][0]
            message = choice['message']

            result = {
                'content': message['content'],
                'model': data['model'],
                'usage': data.get('usage', {}),
                'citations': data.get('citations', []),
                'images': data.get('images', []) if return_images else []
            }

            return result

        except requests.exceptions.RequestException as e:
            raise Exception(f"Failed to perform research: {str(e)}")

    def compare_sources(
        self,
        topic: str,
        sources: List[str],
        temperature: float = 0.2
    ) -> Dict[str, Any]:
        """
        Compare information across multiple sources

        Args:
            topic: Topic to research
            sources: List of source domains or URLs to prioritize
            temperature: Sampling temperature

        Returns:
            Comparative analysis with citations
        """
        system_prompt = f"""
You are a research analyst comparing information across multiple sources.
Focus on these sources: {', '.join(sources)}

For the topic, provide:
1. Key findings from each source
2. Areas of agreement
3. Areas of disagreement or contradiction
4. Source credibility assessment
5. Synthesis and conclusion
"""

        query = f"Compare and analyze information about: {topic}"

        return self.research(
            query=query,
            system_prompt=system_prompt,
            temperature=temperature,
            return_citations=True
        )

    def fact_check(
        self,
        claim: str,
        temperature: float = 0.1
    ) -> Dict[str, Any]:
        """
        Fact-check a specific claim

        Args:
            claim: Claim to verify
            temperature: Lower temperature for more accurate fact-checking

        Returns:
            Fact-check results with evidence and citations
        """
        system_prompt = """
You are a fact-checker. Analyze the claim and provide:
1. Verdict: True / False / Partially True / Unverifiable
2. Evidence supporting or refuting the claim
3. Context and nuance
4. Quality and reliability of sources
5. Date of information (if time-sensitive)
"""

        query = f"Fact-check this claim: {claim}"

        return self.research(
            query=query,
            system_prompt=system_prompt,
            temperature=temperature,
            return_citations=True
        )

    def market_research(
        self,
        topic: str,
        aspects: Optional[List[str]] = None,
        temperature: float = 0.3
    ) -> Dict[str, Any]:
        """
        Conduct market research

        Args:
            topic: Market or product to research
            aspects: Specific aspects to focus on
            temperature: Sampling temperature

        Returns:
            Market research report with citations
        """
        if aspects is None:
            aspects = [
                "market size and growth",
                "key players and competitors",
                "trends and innovations",
                "challenges and opportunities",
                "customer segments",
                "pricing and business models"
            ]

        system_prompt = f"""
You are a market research analyst. Provide comprehensive analysis covering:
{chr(10).join(f'- {aspect}' for aspect in aspects)}

Include recent data, statistics, and expert opinions.
"""

        query = f"Conduct market research on: {topic}"

        return self.research(
            query=query,
            system_prompt=system_prompt,
            temperature=temperature,
            return_citations=True
        )

    def tech_analysis(
        self,
        technology: str,
        depth: str = "comprehensive",
        temperature: float = 0.2
    ) -> Dict[str, Any]:
        """
        Technical analysis of a technology or framework

        Args:
            technology: Technology to analyze
            depth: Analysis depth (quick / standard / comprehensive)
            temperature: Sampling temperature

        Returns:
            Technical analysis with citations
        """
        depth_configs = {
            "quick": "Brief overview focusing on key capabilities and use cases",
            "standard": "Balanced analysis covering capabilities, pros/cons, and use cases",
            "comprehensive": """Deep technical analysis including:
- Technical architecture and components
- Capabilities and features
- Performance characteristics
- Pros and cons
- Use cases and applications
- Comparison with alternatives
- Adoption and ecosystem
- Future outlook"""
        }

        system_prompt = f"""
You are a technical analyst. Provide {depth} analysis.

Focus: {depth_configs.get(depth, depth_configs['standard'])}

Include code examples if relevant.
"""

        query = f"Technical analysis of: {technology}"

        return self.research(
            query=query,
            system_prompt=system_prompt,
            temperature=temperature,
            return_citations=True
        )


def print_research_result(result: Dict[str, Any]) -> None:
    """Pretty print research results"""
    print(f"\n{'='*70}")
    print(f"PERPLEXITY AI RESEARCH")
    print(f"{'='*70}")

    print(f"\nModel: {result.get('model', 'N/A')}")

    if 'usage' in result:
        usage = result['usage']
        print(f"Tokens: {usage.get('total_tokens', 'N/A')} "
              f"(prompt: {usage.get('prompt_tokens', 'N/A')}, "
              f"completion: {usage.get('completion_tokens', 'N/A')})")

    print(f"\n{'-'*70}")
    print("RESEARCH RESULTS:")
    print(f"{'-'*70}\n")

    print(result.get('content', 'No content'))

    if result.get('citations'):
        print(f"\n{'-'*70}")
        print(f"SOURCES ({len(result['citations'])} citations):")
        print(f"{'-'*70}\n")

        for i, citation in enumerate(result['citations'], 1):
            print(f"{i}. {citation}")

    if result.get('images'):
        print(f"\n{'-'*70}")
        print(f"IMAGES ({len(result['images'])} images):")
        print(f"{'-'*70}\n")

        for i, image in enumerate(result['images'], 1):
            print(f"{i}. {image}")

    print(f"\n{'='*70}\n")


def main():
    """CLI for Perplexity AI"""
    parser = argparse.ArgumentParser(
        description="Perplexity AI - Deep Research with Citations",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:

  # Basic research
  python perplexity_helper.py research "What are AI agents in 2025?"

  # Market research
  python perplexity_helper.py market "AI automation tools"

  # Fact check
  python perplexity_helper.py fact-check "Claude 4 has 1M token context"

  # Tech analysis
  python perplexity_helper.py tech "FastAPI framework" --depth comprehensive

  # Compare sources
  python perplexity_helper.py compare "MCP protocol" --sources "anthropic.com" "github.com"
        """
    )

    parser.add_argument(
        '--api-key',
        help='Perplexity API key (or use PERPLEXITY_API_KEY env variable)'
    )

    parser.add_argument(
        '--model',
        help='Model to use (default: llama-3.1-sonar-large-128k-online)'
    )

    subparsers = parser.add_subparsers(dest='command', help='Commands')

    # Research command
    research_parser = subparsers.add_parser('research', help='General research query')
    research_parser.add_argument('query', help='Research question')
    research_parser.add_argument('--temperature', type=float, default=0.2,
                                help='Temperature (0-2)')
    research_parser.add_argument('--max-tokens', type=int, default=4000,
                                help='Max response tokens')

    # Market research
    market_parser = subparsers.add_parser('market', help='Market research')
    market_parser.add_argument('topic', help='Market or product')

    # Fact check
    fact_parser = subparsers.add_parser('fact-check', help='Fact-check a claim')
    fact_parser.add_argument('claim', help='Claim to verify')

    # Tech analysis
    tech_parser = subparsers.add_parser('tech', help='Technology analysis')
    tech_parser.add_argument('technology', help='Technology to analyze')
    tech_parser.add_argument('--depth', choices=['quick', 'standard', 'comprehensive'],
                            default='standard', help='Analysis depth')

    # Compare sources
    compare_parser = subparsers.add_parser('compare', help='Compare sources')
    compare_parser.add_argument('topic', help='Topic to research')
    compare_parser.add_argument('--sources', nargs='+', required=True,
                               help='Sources to compare')

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        sys.exit(1)

    try:
        client = PerplexityClient(api_key=args.api_key, model=args.model)

        if args.command == 'research':
            print(f"Researching: {args.query}")
            result = client.research(
                query=args.query,
                temperature=args.temperature,
                max_tokens=args.max_tokens
            )
            print_research_result(result)

        elif args.command == 'market':
            print(f"Market research: {args.topic}")
            result = client.market_research(topic=args.topic)
            print_research_result(result)

        elif args.command == 'fact-check':
            print(f"Fact-checking: {args.claim}")
            result = client.fact_check(claim=args.claim)
            print_research_result(result)

        elif args.command == 'tech':
            print(f"Technical analysis: {args.technology}")
            result = client.tech_analysis(
                technology=args.technology,
                depth=args.depth
            )
            print_research_result(result)

        elif args.command == 'compare':
            print(f"Comparing sources for: {args.topic}")
            result = client.compare_sources(
                topic=args.topic,
                sources=args.sources
            )
            print_research_result(result)

    except Exception as e:
        print(f"Error: {str(e)}", file=sys.stderr)
        sys.exit(1)


if __name__ == '__main__':
    main()
