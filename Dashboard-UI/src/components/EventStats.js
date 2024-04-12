import React, { useEffect, useState } from "react";

export default function EventStats() {
    const [isLoaded, setIsLoaded] = useState(false)
    const [stats, setStats] = useState({})
    const [error, setError] = useState(null)

    const getStats = () => {
        fetch('http://kafka-acit3855-lab6.eastus.cloudapp.azure.com/event-logger/stats')
            .then(res => res.json())
            .then((result)=>{
                console.log("Received event stats")
                setStats(result)
                setIsLoaded(true)
            })
    }
    useEffect(() => {
        const interval = setInterval(() => getStats(), 2000)
        return() => clearInterval(interval)
    }, [getStats])
    if (error){
        return (<div className={"error"}>Error found when fetching from API</div>)
    } else if (isLoaded === false){
        return(<div>Loading...</div>)
    } else if (isLoaded === true){
        return(
            <div>
                <h1>Latest Event Stats</h1>
                <table className="{eventsTable}">
                    <tbody>
                        <tr>
                            <td>0001: {stats['1']}</td>
                        </tr>
                        <tr>
                            <td>0002: {stats['2']}</td>
                        </tr>
                        <tr>
                            <td>0003: {stats['3']}</td>
                        </tr>
                        <tr>
                            <td>0004: {stats['4']}</td>
                        </tr>
                    </tbody>
                </table>
            </div>
        )
    }
}