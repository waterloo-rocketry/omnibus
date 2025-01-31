import { Line, LineChart, XAxis, YAxis } from 'recharts'
import { useEffect, useState } from 'react';

import './RechartsTester.css';

interface RechartsTesterProps {
  numCharts: number
}

function RechartsTester(props: RechartsTesterProps) {

  var lastUpdated = Date.now();

  const [data, setData] = useState([{
    index: 0,
    a: Math.floor(Math.random() * 500),
    b: Math.floor(Math.random() * 5000),
    c: Math.floor(Math.random() * 3000)
  }]);

  useEffect(() => {
    console.log("Data points per second: ", 1000 / (Date.now() - lastUpdated));
    lastUpdated = Date.now();
  }, [data])

  useEffect(() => {

    var i = 0;

    const interval = setInterval(() => {

      setData((prevData: { index: number; a: number; b: number; c: number; }[]) => {
        prevData = [...prevData, {
          index: i+1,
          a: Math.floor(Math.random() * 500),
          b: Math.floor(Math.random() * 5000),
          c: Math.floor(Math.random() * 3000)
        }];

        return prevData.length > 100 ? prevData.slice(1) : prevData;
      });

      i ++;

    }, 1);

    return () => clearInterval(interval);
  }, []);

  return (
      <div className='flex flex-row flex-wrap'>
      {
        Array.from({ length: props.numCharts }).map((_, index) =>
          <LineChart key={index} width={400} height={300} data={data}>
            <XAxis type="number" dataKey="index" tickCount={8} domain={['dataMin', 'dataMax']} allowDecimals/>
            <YAxis type="number" domain={[0, 'dataMax']} />
            <Line type="monotone" dataKey="a" stroke="#cc6666" dot={false} strokeWidth={2}/>
          </LineChart>
        )
      }
      </div>
  )
}

export default RechartsTester
