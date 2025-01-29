import { CoinAlyzeAPI } from './coinalyze-api';

async function main() {
    const api = new CoinAlyzeAPI({
        apiKey: 'b05fe5d7-dd71-4d78-8a18-856b99f19840'
    });

    try {
        console.log('Attempting to connect to Coinalyze API...');
        
        // Try the simplest endpoint first
        console.log('Fetching exchanges...');
        const exchanges = await api.getSupportedExchanges();
        console.log('Exchanges:', JSON.stringify(exchanges, null, 2));

    } catch (error) {
        if (error instanceof Error) {
            console.error('Error message:', error.message);
            
            // Try to parse the error message if it's JSON
            try {
                const errorBody = JSON.parse(error.message.split(': ')[1]);
                console.error('Parsed error:', errorBody);
            } catch (e) {
                console.error('Raw error:', error.message);
            }
        }
        
        console.error('Full error:', error);
    }
}

main().catch(error => {
    console.error('Unhandled error:', error);
}); 