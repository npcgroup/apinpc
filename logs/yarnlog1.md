```shell
app/ApiDocs.tsx:4:16 - error TS6133: 'TabList' is declared but its value is never read.

4 import { Tabs, TabList, Tab, TabPanel } from './components/Tabs'
                 ~~~~~~~

app/ApiDocs.tsx:4:25 - error TS6133: 'Tab' is declared but its value is never read.

4 import { Tabs, TabList, Tab, TabPanel } from './components/Tabs'
                          ~~~

app/ApiDocs.tsx:2543:8 - error TS6196: 'DataSource' is declared but never used.

2543   type DataSource = typeof dataSources[number]
            ~~~~~~~~~~

app/components/ApiPlayground.tsx:109:23 - error TS6133: 'setCopiedIndex' is declared but its value is never read.

109   const [copiedIndex, setCopiedIndex] = useState<number | null>(null)
                          ~~~~~~~~~~~~~~

app/components/ApiTerminal.tsx:7:30 - error TS2307: Cannot find module '@/lib/formatters' or its corresponding type declarations.

7 import { convertToCSV } from '@/lib/formatters'
                               ~~~~~~~~~~~~~~~~~~

app/components/CodeBlock.tsx:21:8 - error TS2786: 'SyntaxHighlighter' cannot be used as a JSX component.
  Its type 'typeof SyntaxHighlighter' is not a valid JSX element type.
    Types of construct signatures are incompatible.
      Type 'new (props: SyntaxHighlighterProps) => SyntaxHighlighter' is not assignable to type 'new (props: any, deprecatedLegacyContext?: any) => Component<any, any, any>'.
        Property 'refs' is missing in type 'Component<SyntaxHighlighterProps, {}, any>' but required in type 'Component<any, any, any>'.

21       <SyntaxHighlighter
          ~~~~~~~~~~~~~~~~~

  node_modules/@types/react/index.d.ts:1040:9
    1040         refs: {
                 ~~~~
    'refs' is declared here.

app/components/Tabs.tsx:10:45 - error TS6133: 'activeTab' is declared but its value is never read.

10 export const Tabs: React.FC<TabsProps> = ({ activeTab, children }) => {
                                               ~~~~~~~~~

app/components/Tabs.tsx:25:43 - error TS6133: 'id' is declared but its value is never read.

25 export const Tab: React.FC<TabProps> = ({ id, active, onClick, children }) => {
                                             ~~

app/dataingestion.ts:1:26 - error TS2307: Cannot find module '@/lib/supabaseClient' or its corresponding type declarations.

1 import { supabase } from '@/lib/supabaseClient';
                           ~~~~~~~~~~~~~~~~~~~~~~

app/dataingestion.ts:2:1 - error TS6192: All imports in import declaration are unused.

2 import { formatNumber, formatDate } from '@/utils/formatters';
  ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

app/dataingestion.ts:2:42 - error TS2307: Cannot find module '@/utils/formatters' or its corresponding type declarations.

2 import { formatNumber, formatDate } from '@/utils/formatters';
                                           ~~~~~~~~~~~~~~~~~~~~

app/docs/page.tsx:3:17 - error TS6133: 'useEffect' is declared but its value is never read.

3 import React, { useEffect, useState } from 'react';
                  ~~~~~~~~~

app/docs/page.tsx:4:42 - error TS6133: 'GitBranch' is declared but its value is never read.

4 import { Book, Code, Database, FileText, GitBranch, Terminal } from 'lucide-react';
                                           ~~~~~~~~~

app/docs/page.tsx:4:53 - error TS6133: 'Terminal' is declared but its value is never read.

4 import { Book, Code, Database, FileText, GitBranch, Terminal } from 'lucide-react';
                                                      ~~~~~~~~

app/perp-metrics/page.tsx:192:7 - error TS6133: 'fetchMetrics' is declared but its value is never read.

192 const fetchMetrics = async () => {
          ~~~~~~~~~~~~

components/ApiDocs.tsx:4:10 - error TS6133: 'ChevronDown' is declared but its value is never read.

4 import { ChevronDown, ChevronRight, Book, Database, Code, Zap, Search, Terminal } from 'lucide-react';
           ~~~~~~~~~~~

components/ApiDocs.tsx:4:23 - error TS6133: 'ChevronRight' is declared but its value is never read.

4 import { ChevronDown, ChevronRight, Book, Database, Code, Zap, Search, Terminal } from 'lucide-react';
                        ~~~~~~~~~~~~

components/ApiDocs.tsx:5:10 - error TS6133: 'API_EXAMPLES' is declared but its value is never read.

5 import { API_EXAMPLES, DOCUMENTATION_SECTIONS, API_REFERENCE } from '../utils/docExamples';
           ~~~~~~~~~~~~

components/ApiDocs.tsx:5:69 - error TS2307: Cannot find module '../utils/docExamples' or its corresponding type declarations.

5 import { API_EXAMPLES, DOCUMENTATION_SECTIONS, API_REFERENCE } from '../utils/docExamples';
                                                                      ~~~~~~~~~~~~~~~~~~~~~~

components/ApiDocs.tsx:6:34 - error TS2307: Cannot find module '../types/api' or its corresponding type declarations.

6 import type { ApiEndpoint } from '../types/api';
                                   ~~~~~~~~~~~~~~

components/ApiDocs.tsx:50:40 - error TS7006: Parameter 'param' implicitly has an 'any' type.

50               {endpoint.parameters.map(param => (
                                          ~~~~~

components/ApiDocs.tsx:73:37 - error TS7006: Parameter 'example' implicitly has an 'any' type.

73             {endpoint.examples.map((example, index) => (
                                       ~~~~~~~

components/ApiDocs.tsx:73:46 - error TS7006: Parameter 'index' implicitly has an 'any' type.

73             {endpoint.examples.map((example, index) => (
                                                ~~~~~

components/ApiDocs.tsx:161:10 - error TS6133: 'searchResults' is declared but its value is never read.

161   const [searchResults, setSearchResults] = useState<SearchResult[]>([]);
             ~~~~~~~~~~~~~

components/ApiDocs.tsx:161:25 - error TS6133: 'setSearchResults' is declared but its value is never read.

161   const [searchResults, setSearchResults] = useState<SearchResult[]>([]);
                            ~~~~~~~~~~~~~~~~

scripts/ingestData.ts:1:38 - error TS2307: Cannot find module '../services/dataIngestion' or its corresponding type declarations.

1 import { DataIngestionService } from '../services/dataIngestion'
                                       ~~~~~~~~~~~~~~~~~~~~~~~~~~~

scripts/run.ts:6:6 - error TS2339: Property 'token_addresses' does not exist on type 'Window & typeof globalThis'.

6 self.token_addresses = {
       ~~~~~~~~~~~~~~~

scripts/testIngestion.ts:1:38 - error TS2307: Cannot find module '../services/dataIngestion' or its corresponding type declarations.

1 import { DataIngestionService } from '../services/dataIngestion';
                                       ~~~~~~~~~~~~~~~~~~~~~~~~~~~

scripts/testPerpIngestion.ts:20:11 - error TS6196: 'MetricQuality' is declared but never used.

20 interface MetricQuality {
             ~~~~~~~~~~~~~

src/strategies/FundingArbitrage/strategy.ts:9:23 - error TS6138: Property 'config' is declared but its value is never read.

9   constructor(private config: StrategyConfig) {}
                        ~~~~~~

src/strategies/FundingArbitrage/strategy.ts:11:11 - error TS6133: 'metrics' is declared but its value is never read.

11   analyze(metrics: PerpetualMetrics) {
             ~~~~~~~

src/utils/clients/bitqueryClient.ts:2:23 - error TS6138: Property 'apiKey' is declared but its value is never read.

2   constructor(private apiKey: string) {}
                        ~~~~~~

src/utils/clients/duneClient.ts:2:23 - error TS6138: Property 'apiKey' is declared but its value is never read.

2   constructor(private apiKey: string) {}
                        ~~~~~~

src/utils/clients/footprintClient.ts:2:23 - error TS6138: Property 'apiKey' is declared but its value is never read.

2   constructor(private apiKey: string) {}
                        ~~~~~~

src/utils/clients/theGraphClient.ts:2:23 - error TS6138: Property 'apiKey' is declared but its value is never read.

2   constructor(private apiKey: string) {}
                        ~~~~~~

src/utils/naturalLanguageQuery.ts:1:34 - error TS2307: Cannot find module '../types' or its corresponding type declarations.

1 import type { QueryConfig } from '../types'
                                   ~~~~~~~~~~


Found 36 errors in 19 files.

Errors  Files
     3  app/ApiDocs.tsx:4
     1  app/components/ApiPlayground.tsx:109
     1  app/components/ApiTerminal.tsx:7
     1  app/components/CodeBlock.tsx:21
     2  app/components/Tabs.tsx:10
     3  app/dataingestion.ts:1
     3  app/docs/page.tsx:3
     1  app/perp-metrics/page.tsx:192
    10  components/ApiDocs.tsx:4
     1  scripts/ingestData.ts:1
     1  scripts/run.ts:6
     1  scripts/testIngestion.ts:1
     1  scripts/testPerpIngestion.ts:20
     2  src/strategies/FundingArbitrage/strategy.ts:9
     1  src/utils/clients/bitqueryClient.ts:2
     1  src/utils/clients/duneClient.ts:2
     1  src/utils/clients/footprintClient.ts:2
     1  src/utils/clients/theGraphClient.ts:2
     1  src/utils/naturalLanguageQuery.ts:1
error Command failed with exit code 2.
info Visit https://yarnpkg.com/en/docs/cli/run for documentation about this command.
error Command failed with exit code 2.
info Visit https://yarnpkg.com/en/docs/cli/run for documentation about this command.
error Command failed with exit code 2.
info Visit https://yarnpkg.com/en/docs/cli/install for documentation about this command.
❯ yarn install
yarn install v1.22.22
[1/4] 🔍  Resolving packages...
success Already up-to-date.
$ yarn build
yarn run v1.22.22
$ yarn build:clean && yarn build:tsc && yarn build:move
$ rimraf dist
$ tsc -p tsconfig.build.json
app/agent.tsx:497:9 - error TS2353: Object literal may only specify known properties, and 'type' does not exist in type 'QueryConfig'.

497         type: 'track'
            ~~~~

app/agent.tsx:638:69 - error TS2353: Object literal may only specify known properties, and 'apiKey' does not exist in type 'QueryConfig'.

638         const result = await handleNaturalLanguageQuery(question, { apiKey });
                                                                        ~~~~~~

app/ApiDocs.tsx:2543:8 - error TS6196: 'DataSource' is declared but never used.

2543   type DataSource = typeof dataSources[number]
            ~~~~~~~~~~

app/ApiDocs.tsx:2569:15 - error TS2322: Type '{ children: Element[]; activeTab: string; }' is not assignable to type 'IntrinsicAttributes & TabsProps'.
  Property 'activeTab' does not exist on type 'IntrinsicAttributes & TabsProps'.

2569         <Tabs activeTab={activeTab}>
                   ~~~~~~~~~

app/components/ApiPlayground.tsx:109:23 - error TS6133: 'setCopiedIndex' is declared but its value is never read.

109   const [copiedIndex, setCopiedIndex] = useState<number | null>(null)
                          ~~~~~~~~~~~~~~

app/components/CodeBlock.tsx:15:8 - error TS2786: 'SyntaxHighlighter' cannot be used as a JSX component.
  Its type 'typeof SyntaxHighlighter' is not a valid JSX element type.
    Types of construct signatures are incompatible.
      Type 'new (props: SyntaxHighlighterProps) => SyntaxHighlighter' is not assignable to type 'new (props: any, deprecatedLegacyContext?: any) => Component<any, any, any>'.
        Property 'refs' is missing in type 'Component<SyntaxHighlighterProps, {}, any>' but required in type 'Component<any, any, any>'.

15       <SyntaxHighlighter
          ~~~~~~~~~~~~~~~~~

  node_modules/@types/react/index.d.ts:1040:9
    1040         refs: {
                 ~~~~
    'refs' is declared here.

app/components/CodeBlock.tsx:17:9 - error TS2322: Type '{ 'code[class*="language-"]': { color: string; background: string; fontFamily: string; fontSize: string; textAlign: string; whiteSpace: string; wordSpacing: string; wordBreak: string; wordWrap: string; lineHeight: string; tabSize: string; hyphens: string; }; ... 34 more ...; inserted: { ...; }; }' is not assignable to type '{ [key: string]: CSSProperties; }'.
  Property ''code[class*="language-"]'' is incompatible with index signature.
    Type '{ color: string; background: string; fontFamily: string; fontSize: string; textAlign: string; whiteSpace: string; wordSpacing: string; wordBreak: string; wordWrap: string; lineHeight: string; tabSize: string; hyphens: string; }' is not assignable to type 'CSSProperties'.
      Types of property 'hyphens' are incompatible.
        Type 'string' is not assignable to type 'Hyphens | undefined'.

17         style={tomorrow}
           ~~~~~

  node_modules/@types/react-syntax-highlighter/index.d.ts:19:9
    19         style?: { [key: string]: React.CSSProperties } | undefined;
               ~~~~~
    The expected type comes from property 'style' which is declared here on type 'IntrinsicAttributes & IntrinsicClassAttributes<SyntaxHighlighter> & Readonly<SyntaxHighlighterProps>'

app/dataingestion.ts:2:1 - error TS6192: All imports in import declaration are unused.

2 import { formatNumber, formatDate } from '@/utils/formatters';
  ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

app/dataingestion.ts:2:42 - error TS2307: Cannot find module '@/utils/formatters' or its corresponding type declarations.

2 import { formatNumber, formatDate } from '@/utils/formatters';
                                           ~~~~~~~~~~~~~~~~~~~~

app/docs/page.tsx:3:17 - error TS6133: 'useEffect' is declared but its value is never read.

3 import React, { useEffect, useState } from 'react';
                  ~~~~~~~~~

app/docs/page.tsx:4:42 - error TS6133: 'GitBranch' is declared but its value is never read.

4 import { Book, Code, Database, FileText, GitBranch, Terminal } from 'lucide-react';
                                           ~~~~~~~~~

app/docs/page.tsx:4:53 - error TS6133: 'Terminal' is declared but its value is never read.

4 import { Book, Code, Database, FileText, GitBranch, Terminal } from 'lucide-react';
                                                      ~~~~~~~~

app/perp-metrics/page.tsx:192:7 - error TS6133: 'fetchMetrics' is declared but its value is never read.

192 const fetchMetrics = async () => {
          ~~~~~~~~~~~~

components/ApiDocs.tsx:4:10 - error TS6133: 'ChevronDown' is declared but its value is never read.

4 import { ChevronDown, ChevronRight, Book, Database, Code, Zap, Search, Terminal } from 'lucide-react';
           ~~~~~~~~~~~

components/ApiDocs.tsx:4:23 - error TS6133: 'ChevronRight' is declared but its value is never read.

4 import { ChevronDown, ChevronRight, Book, Database, Code, Zap, Search, Terminal } from 'lucide-react';
                        ~~~~~~~~~~~~

components/ApiDocs.tsx:5:10 - error TS6133: 'API_EXAMPLES' is declared but its value is never read.

5 import { API_EXAMPLES, DOCUMENTATION_SECTIONS, API_REFERENCE } from '../utils/docExamples';
           ~~~~~~~~~~~~

components/ApiDocs.tsx:5:69 - error TS2307: Cannot find module '../utils/docExamples' or its corresponding type declarations.

5 import { API_EXAMPLES, DOCUMENTATION_SECTIONS, API_REFERENCE } from '../utils/docExamples';
                                                                      ~~~~~~~~~~~~~~~~~~~~~~

components/ApiDocs.tsx:6:34 - error TS2307: Cannot find module '../types/api' or its corresponding type declarations.

6 import type { ApiEndpoint } from '../types/api';
                                   ~~~~~~~~~~~~~~

components/ApiDocs.tsx:50:40 - error TS7006: Parameter 'param' implicitly has an 'any' type.

50               {endpoint.parameters.map(param => (
                                          ~~~~~

components/ApiDocs.tsx:73:37 - error TS7006: Parameter 'example' implicitly has an 'any' type.

73             {endpoint.examples.map((example, index) => (
                                       ~~~~~~~

components/ApiDocs.tsx:73:46 - error TS7006: Parameter 'index' implicitly has an 'any' type.

73             {endpoint.examples.map((example, index) => (
                                                ~~~~~

components/ApiDocs.tsx:161:10 - error TS6133: 'searchResults' is declared but its value is never read.

161   const [searchResults, setSearchResults] = useState<SearchResult[]>([]);
             ~~~~~~~~~~~~~

components/ApiDocs.tsx:161:25 - error TS6133: 'setSearchResults' is declared but its value is never read.

161   const [searchResults, setSearchResults] = useState<SearchResult[]>([]);
                            ~~~~~~~~~~~~~~~~

scripts/ingestAndStore.ts:10:39 - error TS2339: Property 'testSupabaseConnection' does not exist on type 'DataIngestionService'.

10     const isConnected = await service.testSupabaseConnection();
                                         ~~~~~~~~~~~~~~~~~~~~~~

scripts/ingestAndStore.ts:19:56 - error TS2339: Property 'fetchCombinedMarketData' does not exist on type 'DataIngestionService'.

19         const { birdeye, hyperliquid } = await service.fetchCombinedMarketData(symbol, address);
                                                          ~~~~~~~~~~~~~~~~~~~~~~~

scripts/ingestAndStore.ts:38:23 - error TS2339: Property 'ingestMetrics' does not exist on type 'DataIngestionService'.

38         await service.ingestMetrics([metric]);
                         ~~~~~~~~~~~~~

scripts/ingestData.ts:1:38 - error TS2307: Cannot find module '../services/dataIngestion' or its corresponding type declarations.

1 import { DataIngestionService } from '../services/dataIngestion'
                                       ~~~~~~~~~~~~~~~~~~~~~~~~~~~

scripts/run.ts:6:6 - error TS2339: Property 'token_addresses' does not exist on type 'Window & typeof globalThis'.

6 self.token_addresses = {
       ~~~~~~~~~~~~~~~

scripts/testDataIngestion.ts:17:39 - error TS2339: Property 'testConnection' does not exist on type 'DataIngestionService'.

17     const isConnected = await service.testConnection()
                                         ~~~~~~~~~~~~~~

scripts/testDataIngestion.ts:33:15 - error TS2339: Property 'fetchBirdeyeData' does not exist on type 'DataIngestionService'.

33       service.fetchBirdeyeData(testAddress).catch(error => {
                 ~~~~~~~~~~~~~~~~

scripts/testDataIngestion.ts:33:51 - error TS7006: Parameter 'error' implicitly has an 'any' type.

33       service.fetchBirdeyeData(testAddress).catch(error => {
                                                     ~~~~~

scripts/testDataIngestion.ts:35:24 - error TS2339: Property 'getDefaultTokenData' does not exist on type 'DataIngestionService'.

35         return service.getDefaultTokenData()
                          ~~~~~~~~~~~~~~~~~~~

scripts/testDataIngestion.ts:37:15 - error TS2339: Property 'fetchDexScreenerData' does not exist on type 'DataIngestionService'.

37       service.fetchDexScreenerData(testAddress).catch(error => {
                 ~~~~~~~~~~~~~~~~~~~~

scripts/testDataIngestion.ts:37:55 - error TS7006: Parameter 'error' implicitly has an 'any' type.

37       service.fetchDexScreenerData(testAddress).catch(error => {
                                                         ~~~~~

scripts/testDataIngestion.ts:39:24 - error TS2339: Property 'getDefaultDexData' does not exist on type 'DataIngestionService'.

39         return service.getDefaultDexData()
                          ~~~~~~~~~~~~~~~~~

scripts/testDataIngestion.ts:41:36 - error TS2554: Expected 0 arguments, but got 1.

41       service.fetchHyperliquidData(testSymbol).catch(error => {
                                      ~~~~~~~~~~

scripts/testDataIngestion.ts:43:24 - error TS2339: Property 'getDefaultMarketData' does not exist on type 'DataIngestionService'.

43         return service.getDefaultMarketData()
                          ~~~~~~~~~~~~~~~~~~~~

scripts/testDataIngestion.ts:66:19 - error TS2339: Property 'ingestMetrics' does not exist on type 'DataIngestionService'.

66     await service.ingestMetrics([metric])
                     ~~~~~~~~~~~~~

scripts/testIngestion.ts:1:38 - error TS2307: Cannot find module '../services/dataIngestion' or its corresponding type declarations.

1 import { DataIngestionService } from '../services/dataIngestion';
                                       ~~~~~~~~~~~~~~~~~~~~~~~~~~~

scripts/testPerpIngestion.ts:20:11 - error TS6196: 'MetricQuality' is declared but never used.

20 interface MetricQuality {
             ~~~~~~~~~~~~~

scripts/testPerpIngestion.ts:213:55 - error TS2339: Property 'testSupabaseConnection' does not exist on type 'DataIngestionService'.

213       const isConnected = await this.ingestionService.testSupabaseConnection();
                                                          ~~~~~~~~~~~~~~~~~~~~~~

src/services/dataIngestion.ts:1:1 - error TS6133: 'supabase' is declared but its value is never read.

1 import { supabase } from '@/lib/supabaseClient';
  ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

src/strategies/FundingArbitrage/strategy.ts:9:23 - error TS6138: Property 'config' is declared but its value is never read.

9   constructor(private config: StrategyConfig) {}
                        ~~~~~~

src/strategies/FundingArbitrage/strategy.ts:11:11 - error TS6133: 'metrics' is declared but its value is never read.

11   analyze(metrics: PerpetualMetrics) {
             ~~~~~~~

src/utils/clients/duneClient.ts:2:23 - error TS6138: Property 'apiKey' is declared but its value is never read.

2   constructor(private apiKey: string) {}
                        ~~~~~~

src/utils/clients/footprintClient.ts:2:23 - error TS6138: Property 'apiKey' is declared but its value is never read.

2   constructor(private apiKey: string) {}
                        ~~~~~~

src/utils/clients/theGraphClient.ts:2:23 - error TS6138: Property 'apiKey' is declared but its value is never read.

2   constructor(private apiKey: string) {}
                        ~~~~~~

src/utils/naturalLanguageQuery.ts:5:3 - error TS2741: Property 'query' is missing in type '{}' but required in type 'QueryConfig'.

5   config: QueryConfig = {}
    ~~~~~~~~~~~~~~~~~~~~~~~~

  src/types/index.ts:2:3
    2   query: string;
        ~~~~~
    'query' is declared here.


Found 48 errors in 20 files.

Errors  Files
     2  app/agent.tsx:497
     2  app/ApiDocs.tsx:2543
     1  app/components/ApiPlayground.tsx:109
     2  app/components/CodeBlock.tsx:15
     2  app/dataingestion.ts:2
     3  app/docs/page.tsx:3
     1  app/perp-metrics/page.tsx:192
    10  components/ApiDocs.tsx:4
     3  scripts/ingestAndStore.ts:10
     1  scripts/ingestData.ts:1
     1  scripts/run.ts:6
    10  scripts/testDataIngestion.ts:17
     1  scripts/testIngestion.ts:1
     2  scripts/testPerpIngestion.ts:20
     1  src/services/dataIngestion.ts:1
     2  src/strategies/FundingArbitrage/strategy.ts:9
     1  src/utils/clients/duneClient.ts:2
     1  src/utils/clients/footprintClient.ts:2
     1  src/utils/clients/theGraphClient.ts:2
     1  src/utils/naturalLanguageQuery.ts:5
error Command failed with exit code 2.
info Visit https://yarnpkg.com/en/docs/cli/run for documentation about this command.
error Command failed with exit code 2.
info Visit https://yarnpkg.com/en/docs/cli/run for documentation about this command.
error Command failed with exit code 2.
info Visit https://yarnpkg.com/en/docs/cli/install for documentation about this command.
    ~/Doc/G/apinpc    stable-test !13 ?6                2 ✘  7s   lot   17:56:09  
 ```        