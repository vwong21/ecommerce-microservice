import React, { useState, useEffect } from "react";
import "../App.css";

export default function AnomalyStats() {
  const [isLoaded, setIsLoaded] = useState(false);
  const [productStats, setProductStats] = useState({});
  const [orderStats, setOrderStats] = useState({});
  const [error, setError] = useState(null);

  const getStats = (anomalyType) => {
    fetch(
      `http://kafka-acit3855-lab6.eastus.cloudapp.azure.com/anomaly-detector/anomaly_stats?anomaly_type=${anomalyType}`
    )
      .then((res) => res.json())
      .then(
        (result) => {
          console.log(`Received anomaly_stats for ${anomalyType}`);
          if (anomalyType === "products") {
            setProductStats(result);
          } else if (anomalyType === "orders") {
            setOrderStats(result);
          }
          setIsLoaded(true);
        },
        (error) => {
          setError(error);
          setIsLoaded(true);
        }
      );
  };

  useEffect(() => {
    const interval = setInterval(() => {
      getStats("products");
      getStats("orders");
    }, 4000); // Update every 4 seconds
    return () => clearInterval(interval);
  }, []);

  return (
    <div>
      <h2>Product Stats</h2>
      <p>Number of anomalies: {productStats.num_anomalies}</p>
      <p>Most recent description: {productStats.most_recent_desc}</p>
      <p>Most recent datetime: {productStats.most_recent_datetime}</p>

      <h2>Order Stats</h2>
      <p>Number of anomalies: {orderStats.num_anomalies}</p>
      <p>Most recent description: {orderStats.most_recent_desc}</p>
      <p>Most recent datetime: {orderStats.most_recent_datetime}</p>
    </div>
  );
}
