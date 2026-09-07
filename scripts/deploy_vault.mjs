import fs from 'fs';
import path from 'path';
import { fileURLToPath } from 'url';
import { createClient, createAccount } from '../../AetherDungeon/frontend/node_modules/genlayer-js/dist/index.js';

const __dirname = path.dirname(fileURLToPath(import.meta.url));

async function main() {
    console.log("Connecting to GenLayer Studio RPC: https://studio.genlayer.com/api");
    const account = createAccount();
    console.log("Generated Deployer / Owner Account:", account.address);
    
    const client = createClient({
        endpoint: 'https://studio.genlayer.com/api',
        account: account
    });
    
    const contractPath = path.join(__dirname, '..', 'agent_capability_vault.py');
    const code = fs.readFileSync(contractPath, 'utf8');
    console.log(`Read contract code (${code.length} bytes)`);
    
    const owner = account.address;
    
    console.log("Broadcasting deployContract transaction to GenLayer Studio...");
    try {
        const txHash = await client.deployContract({
            code: code,
            args: [owner]
        });
        console.log("Deployment transaction submitted! Tx Hash:", txHash);
        
        console.log("Waiting for transaction receipt on GenLayer (status: FINALIZED)...");
        const receipt = await client.waitForTransactionReceipt({
            hash: txHash,
            status: 'FINALIZED',
            interval: 3000,
            retries: 50
        });
        console.log("Receipt status:", receipt.status);
        const contractAddress = receipt.contractAddress || receipt.data?.contractAddress || receipt.recipient;
        console.log("Contract Address:", contractAddress);
        
        if (contractAddress) {
            console.log("\n>>> DEPLOYMENT SUCCESSFUL! <<<");
            console.log("Deployed AgentCapabilityVault Address:", contractAddress);
            console.log("Explorer URL: https://explorer-studio.genlayer.com/address/" + contractAddress);

            // Test on-chain read calls
            const total = await client.readContract({
                address: contractAddress,
                functionName: 'get_total_agents',
                args: []
            });
            console.log("Total agents count:", total);

            const a1 = await client.readContract({
                address: contractAddress,
                functionName: 'get_agent_vault',
                args: ['AGENT_1']
            });
            console.log("\nSeed AGENT_1 Details:");
            console.log("- Status:", a1?.status);
            console.log("- Endpoint:", a1?.agent_endpoint);
            console.log("- Capability:", a1?.claimed_capability);
            console.log("- Staked Deposit:", a1?.staked_deposit);

            const a2 = await client.readContract({
                address: contractAddress,
                functionName: 'get_agent_vault',
                args: ['AGENT_2']
            });
            console.log("\nSeed AGENT_2 Details:");
            console.log("- Status:", a2?.status);
            console.log("- Endpoint:", a2?.agent_endpoint);
            console.log("- Capability:", a2?.claimed_capability);
            console.log("- Staked Deposit:", a2?.staked_deposit);
        }
    } catch (err) {
        console.error("Deployment failed:", err);
    }
}

main();
