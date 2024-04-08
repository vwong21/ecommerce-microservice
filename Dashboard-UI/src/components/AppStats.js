import React, { useEffect, useState } from 'react'
import '../App.css';

export default function AppStats() {
    const [isLoaded, setIsLoaded] = useState(false);
    const [stats, setStats] = useState({});
    const [error, setError] = useState(null)

	const getStats = () => {
	
        fetch(`http://kafka-acit3855-lab6.eastus.cloudapp.azure.com/processing/stats`)
            .then(res => res.json())
            .then((result)=>{
				console.log("Received Stats")
                setStats(result);
                setIsLoaded(true);
            },(error) =>{
                setError(error)
                setIsLoaded(true);
            })
    }
    useEffect(() => {
		const interval = setInterval(() => getStats(), 2000); // Update every 2 seconds
		return() => clearInterval(interval);
    }, [getStats]);

    if (error){
        return (<div className={"error"}>Error found when fetching from API</div>)
    } else if (isLoaded === false){
        return(<div>Loading...</div>)
    } else if (isLoaded === true){
        return(
            <div>
                <h1>Latest Stats</h1>
                <table className={"StatsTable"}>
					<tbody>
						<tr>
							<th>Products</th>
							<th>Orders</th>
						</tr>
						<tr>
							<td># Products: {stats['number_products']}</td>
							<td># Orders: {stats['number_orders']}</td>
						</tr>
						<tr>
							<td colspan="2">Highest Product Price: {stats['highest_product_price']}</td>
						</tr>
						<tr>
							<td colspan="2">Highest Order Price: {stats['highest_order_price']}</td>
						</tr>
						<tr>
							<td colspan="2">Highest Product Quantity: {stats['highest_product_quantity']}</td>
						</tr>
					</tbody>
                </table>
                <h3>Highest Order Quantity: {stats['highest_order_quantity']}</h3>

            </div>
        )
    }
}
