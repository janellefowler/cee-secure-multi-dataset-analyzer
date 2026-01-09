import openai
import os
import json
import pandas as pd
from typing import Dict, List, Any, Optional
import logging
import re

class NaturalLanguageProcessor:
    """Handles natural language queries and converts them to analytics operations"""
    
    def __init__(self):
        openai.api_key = os.getenv('OPENAI_API_KEY')
        self.query_patterns = self._initialize_patterns()
        
    def _initialize_patterns(self) -> Dict[str, str]:
        """Initialize common query patterns"""
        return {
            'correlation': r'correlat|relationship|impact|affect|influence',
            'comparison': r'compare|versus|vs|difference|better|worse',
            'trend': r'trend|over time|timeline|change|growth|decline',
            'segmentation': r'segment|group|category|type|accredited|certified',
            'performance': r'performance|success|effective|rate|cycle|win',
            'content_gaps': r'gap|missing|not found|improve|need|lacking'
        }
    
    def process_query(self, query: str, data: pd.DataFrame) -> Dict[str, Any]:
        """Process natural language query and return analysis results"""
        try:
            # First, try to understand the query intent
            intent = self._classify_query_intent(query)
            
            # Extract key entities from the query
            entities = self._extract_entities(query)
            
            # Generate analysis based on intent and entities
            analysis_result = self._execute_analysis(intent, entities, data)
            
            return {
                'query': query,
                'intent': intent,
                'entities': entities,
                'analysis': analysis_result,
                'success': True
            }
            
        except Exception as e:
            logging.error(f"Error processing query: {str(e)}")
            return {
                'query': query,
                'error': str(e),
                'success': False
            }
    
    def _classify_query_intent(self, query: str) -> str:
        """Classify the intent of the user query"""
        query_lower = query.lower()
        
        # Check for specific patterns
        for intent, pattern in self.query_patterns.items():
            if re.search(pattern, query_lower):
                return intent
        
        # Default to general analysis
        return 'general_analysis'
    
    def _extract_entities(self, query: str) -> Dict[str, List[str]]:
        """Extract key entities from the query"""
        entities = {
            'metrics': [],
            'dimensions': [],
            'filters': [],
            'timeframes': []
        }
        
        query_lower = query.lower()
        
        # Common metrics
        metric_patterns = {
            'deal_cycle': r'deal cycle|cycle time|sales cycle',
            'win_rate': r'win rate|success rate|close rate',
            'content_found': r'content found|find content|discover',
            'time_spent': r'time spent|usage time|engagement',
            'accreditation': r'accredited|certified|training'
        }
        
        for metric, pattern in metric_patterns.items():
            if re.search(pattern, query_lower):
                entities['metrics'].append(metric)
        
        # Common dimensions
        dimension_patterns = {
            'seller_accredited': r'seller.*accredited|accredited.*seller',
            'sm_accredited': r'manager.*accredited|accredited.*manager|sm.*accredited',
            'content_category': r'content.*category|category.*content|private pricing|product info',
            'usage_level': r'high usage|low usage|frequent|occasional'
        }
        
        for dimension, pattern in dimension_patterns.items():
            if re.search(pattern, query_lower):
                entities['dimensions'].append(dimension)
        
        return entities
    
    def _execute_analysis(self, intent: str, entities: Dict[str, List[str]], data: pd.DataFrame) -> Dict[str, Any]:
        """Execute analysis based on classified intent and entities"""
        from .analytics_engine import ContentEffectivenessAnalyzer
        
        analyzer = ContentEffectivenessAnalyzer(data)
        
        if intent == 'correlation':
            return self._handle_correlation_query(entities, analyzer, data)
        elif intent == 'comparison':
            return self._handle_comparison_query(entities, analyzer, data)
        elif intent == 'segmentation':
            return self._handle_segmentation_query(entities, analyzer, data)
        elif intent == 'performance':
            return self._handle_performance_query(entities, analyzer, data)
        elif intent == 'content_gaps':
            return analyzer.identify_content_gaps()
        else:
            return analyzer.generate_insights_summary()
    
    def _handle_correlation_query(self, entities: Dict[str, List[str]], analyzer, data: pd.DataFrame) -> Dict[str, Any]:
        """Handle correlation-type queries"""
        results = {}
        
        # Check for specific correlation requests
        if 'deal_cycle' in entities['metrics'] and 'time_spent' in entities['metrics']:
            results.update(analyzer.analyze_deal_cycle_correlation())
        
        if 'accreditation' in entities['metrics']:
            results.update(analyzer.analyze_manager_impact())
        
        if not results:
            # Default correlation analysis
            results = analyzer.analyze_deal_cycle_correlation()
        
        return results
    
    def _handle_comparison_query(self, entities: Dict[str, List[str]], analyzer, data: pd.DataFrame) -> Dict[str, Any]:
        """Handle comparison-type queries"""
        results = {}
        
        # Compare accredited vs non-accredited
        if 'seller_accredited' in entities['dimensions'] or 'accreditation' in entities['metrics']:
            accredited_stats = data[data['seller_accredited'] == True].describe()
            non_accredited_stats = data[data['seller_accredited'] == False].describe()
            
            results['accredited_comparison'] = {
                'accredited': accredited_stats.to_dict(),
                'non_accredited': non_accredited_stats.to_dict()
            }
        
        # Add manager impact comparison
        results.update(analyzer.analyze_manager_impact())
        
        return results
    
    def _handle_segmentation_query(self, entities: Dict[str, List[str]], analyzer, data: pd.DataFrame) -> Dict[str, Any]:
        """Handle segmentation-type queries"""
        results = {}
        
        # Segment by accreditation
        if 'accreditation' in entities['metrics'] or 'seller_accredited' in entities['dimensions']:
            results.update(analyzer.analyze_manager_impact())
        
        # Segment by usage level
        if 'usage_level' in entities['dimensions']:
            median_usage = data['time_spent_minutes'].median()
            data['usage_segment'] = data['time_spent_minutes'].apply(
                lambda x: 'High Usage' if x > median_usage else 'Low Usage'
            )
            
            segment_stats = data.groupby('usage_segment').agg({
                'deal_cycle_days': ['mean', 'count'],
                'win_rate': 'mean',
                'content_found': 'mean'
            }).round(2)
            
            results['usage_segmentation'] = segment_stats.to_dict()
        
        return results
    
    def _handle_performance_query(self, entities: Dict[str, List[str]], analyzer, data: pd.DataFrame) -> Dict[str, Any]:
        """Handle performance-type queries"""
        return analyzer.generate_insights_summary()
    
    def generate_natural_response(self, query: str, analysis_results: Dict[str, Any]) -> str:
        """Generate natural language response from analysis results"""
        try:
            # Use OpenAI to generate a natural response
            prompt = self._create_response_prompt(query, analysis_results)
            
            from openai import OpenAI
            client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))
            
            response = client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": "You are a data analyst explaining insights from a Content Effectiveness Engine. Provide clear, actionable insights in business language. Be conversational and focus on what matters most to sales teams."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=500,
                temperature=0.3
            )
            
            return response.choices[0].message.content
            
        except Exception as e:
            logging.error(f"Error generating natural response: {str(e)}")
            return self._generate_fallback_response(analysis_results)
    
    def _create_response_prompt(self, query: str, results: Dict[str, Any]) -> str:
        """Create prompt for natural language response generation"""
        prompt = f"""
        User Query: {query}
        
        Analysis Results: {json.dumps(results, indent=2, default=str)}
        
        Please provide a clear, business-focused response that:
        1. Directly answers the user's question
        2. Highlights key insights and metrics
        3. Provides actionable recommendations
        4. Uses percentages and specific numbers where available
        5. Keeps the response concise but informative
        """
        return prompt
    
    def _generate_fallback_response(self, results: Dict[str, Any]) -> str:
        """Generate fallback response when OpenAI is not available"""
        if 'key_metrics' in results:
            metrics = results['key_metrics']
            
            # Start with a conversational opening
            response = "Here's what I found in your data:\n\n"
            
            # Add key metrics in natural language
            if 'total_interactions' in metrics:
                total = metrics['total_interactions']
                if isinstance(total, (int, float)):
                    response += f"I analyzed {total:,} seller interactions. "
                else:
                    response += f"I analyzed {total} seller interactions. "
            
            if 'content_found_rate' in metrics:
                rate = metrics['content_found_rate']
                if isinstance(rate, str) and '%' in rate:
                    response += f"Sellers successfully found content {rate} of the time. "
                elif isinstance(rate, (int, float)):
                    response += f"Sellers successfully found content {rate:.1%} of the time. "
                else:
                    response += f"Sellers successfully found content {rate} of the time. "
            
            if 'avg_deal_cycle' in metrics:
                cycle = metrics['avg_deal_cycle']
                if isinstance(cycle, str):
                    response += f"The average deal cycle is {cycle}."
                elif isinstance(cycle, (int, float)):
                    response += f"The average deal cycle is {cycle:.1f} days."
                else:
                    response += f"The average deal cycle is {cycle}."
            
            response += "\n\n"
            
            # Add insights in natural language
            if 'actionable_insights' in results and results['actionable_insights']:
                response += "**Key findings:**\n"
                for insight in results['actionable_insights']:
                    # Clean up the insight text
                    clean_insight = str(insight).replace('_', ' ').replace('"', '')
                    response += f"• {clean_insight}\n"
            
            # Add specific analysis insights
            if 'detailed_analyses' in results:
                analyses = results['detailed_analyses']
                
                if 'manager_impact' in analyses and 'best_performing_combo' in analyses['manager_impact']:
                    best = analyses['manager_impact']['best_performing_combo']
                    if isinstance(best, dict):
                        combo = best.get('combination', 'Unknown')
                        cycle = best.get('avg_deal_cycle', 0)
                        win_rate = best.get('win_rate', 0)
                        
                        if isinstance(cycle, (int, float)) and isinstance(win_rate, (int, float)):
                            response += f"\n💡 **Best performance:** {combo} with {cycle:.1f} day cycles and {win_rate:.1%} win rate."
                        else:
                            response += f"\n💡 **Best performance:** {combo}"
                
                if 'highspot_effectiveness' in analyses:
                    he = analyses['highspot_effectiveness']
                    if 'accreditation_significance' in he and isinstance(he['accreditation_significance'], dict):
                        if he['accreditation_significance'].get('significant'):
                            response += "\n✅ **Accreditation impact:** Makes a significant difference in content discovery success."
                        else:
                            response += "\n📊 **Accreditation impact:** Shows some effect but not statistically significant."
                
                if 'content_gaps' in analyses and 'difficult_search_scenarios' in analyses['content_gaps']:
                    gaps = analyses['content_gaps']['difficult_search_scenarios']
                    if isinstance(gaps, (int, float)):
                        response += f"\n⚠️ **Content gaps:** Found {gaps} instances where sellers had difficulty finding content."
            
            return response
        
        return "I've completed the analysis of your data. The results show various patterns in seller behavior and content effectiveness that could help improve your sales process."