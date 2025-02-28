import os
from supabase import create_client
from dotenv import load_dotenv
import pandas as pd
from datetime import datetime
from rich.console import Console
from rich.table import Table
import json

console = Console()

class SupabaseSchemaAnalyzer:
    def __init__(self):
        load_dotenv()
        self.supabase = create_client(
            os.getenv('NEXT_PUBLIC_SUPABASE_URL'),
            os.getenv('NEXT_PUBLIC_SUPABASE_KEY')
        )
        
    async def get_all_schemas(self) -> list:
        """Get all schema names from the database"""
        try:
            response = await self.supabase.rpc(
                'get_schemas',
                {'exclude_schemas': ['pg_catalog', 'information_schema']}
            ).execute()
            return response.data
        except Exception as e:
            console.print(f"[red]Error fetching schemas: {str(e)}[/red]")
            return ['public']  # Fallback to public schema

    async def analyze_table(self, schema: str, table_name: str) -> dict:
        """Analyze a single table's structure and data"""
        try:
            # Get table structure
            query = (
                'columns:information_schema.columns!inner('
                'column_name,data_type,column_default,is_nullable,'
                'character_maximum_length,numeric_precision,numeric_scale),'
                'constraints:information_schema.table_constraints!inner('
                'constraint_type,constraint_name),'
                'foreign_keys:information_schema.key_column_usage!inner('
                'column_name,referenced_table_schema,referenced_table_name,'
                'referenced_column_name)'
            )
            
            # Get table structure
            client = self.supabase
            metadata = getattr(client, 'from')('_metadata')
            metadata_query = getattr(metadata, 'select')(query)
            filtered_query = getattr(metadata_query, 'eq')('table_schema', schema)
            filtered_query = getattr(filtered_query, 'eq')('table_name', table_name)
            response = await getattr(filtered_query, 'execute')()

            # Get sample data and row count
            table_ref = getattr(client, 'from')(f"{schema}.{table_name}")
            table_query = getattr(table_ref, 'select')('*', count='exact')
            limited_query = getattr(table_query, 'limit')(1)
            data_response = await getattr(limited_query, 'execute')()
            
            return {
                'schema': schema,
                'table_name': table_name,
                'structure': response.data[0] if response.data else {},
                'row_count': data_response.count if hasattr(data_response, 'count') else 0,
                'sample_data': data_response.data[0] if data_response.data else None
            }
        except Exception as e:
            console.print(f"[red]Error analyzing {schema}.{table_name}: {str(e)}[/red]")
            return {'error': str(e)}

    async def analyze_all_tables(self) -> dict:
        """Analyze all tables across all schemas"""
        schemas = await self.get_all_schemas()
        analysis = {}

        for schema in schemas:
            try:
                # Get all tables in schema
                tables_response = await self.supabase.rpc(
                    'get_tables',
                    {'schema_name': schema}
                ).execute()
                
                tables = tables_response.data
                analysis[schema] = {}

                for table in tables:
                    try:
                        analysis[schema][table] = await self.analyze_table(schema, table)
                        console.print(f"[green]✓ Analyzed {schema}.{table}[/green]")
                    except Exception as e:
                        console.print(f"[red]Error analyzing {schema}.{table}: {str(e)}[/red]")
                        analysis[schema][table] = {'error': str(e)}

            except Exception as e:
                console.print(f"[red]Error processing schema {schema}: {str(e)}[/red]")

        return analysis

    def generate_report(self, analysis: dict):
        """Generate comprehensive reports"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # Generate JSON report
        with open(f'schema_analysis_{timestamp}.json', 'w') as f:
            json.dump(analysis, f, indent=2)
        
        # Generate Markdown report
        with open(f'schema_analysis_{timestamp}.md', 'w') as f:
            f.write("# Supabase Schema Analysis Report\n\n")
            f.write(f"Generated at: {timestamp}\n\n")
            
            for schema, tables in analysis.items():
                f.write(f"## {schema}\n\n")
                for table_name, table_data in tables.items():
                    if 'error' in table_data:
                        f.write(f"Error: {table_data['error']}\n\n")
                        continue
                    
                    f.write(f"Table: {table_name}\n\n")
                    f.write("### Structure\n\n")
                    f.write(f"{json.dumps(table_data['structure'])}\n\n")
                    f.write("### Row Count\n\n")
                    f.write(f"{table_data['row_count']}\n\n")
                    f.write("### Sample Data\n\n")
                    f.write(f"{table_data['sample_data']}\n\n")
        
        # Print summary to console
        table = Table(title="Schema Analysis Summary")
        table.add_column("Schema")
        table.add_column("Table")
        table.add_column("Row Count")
        table.add_column("Column Count")
        
        for schema, tables in analysis.items():
            for table_name, table_data in tables.items():
                if 'error' not in table_data:
                    table.add_row(
                        schema,
                        table_name,
                        str(table_data['row_count']),
                        str(len(table_data['structure']))
                    )
        
        console.print(table)

async def main():
    analyzer = SupabaseSchemaAnalyzer()
    console.print("[cyan]Starting complete Supabase schema analysis...[/cyan]")
    
    analysis = await analyzer.analyze_all_tables()
    analyzer.generate_report(analysis)
    
    console.print("\n[green]Analysis complete! Reports generated:[/green]")
    console.print("1. schema_analysis_<timestamp>.json")
    console.print("2. schema_analysis_<timestamp>.md")

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())