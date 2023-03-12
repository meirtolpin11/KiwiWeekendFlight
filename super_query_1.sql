select fly_from, fly_to, discount_price, airlines, ROUND((JULIANDAY(departure_from) - JULIANDAY(arrival_to))*24) AS hours, case cast (strftime('%w', departure_to) as integer)
  when 0 then 'Sunday'
  when 1 then 'Monday'
  when 2 then 'Tuesday'
  when 3 then 'Wednesday'
  when 4 then 'Thursday'
  when 5 then 'Friday'
  else 'Saturday' end as departure_to_day,departure_to, case cast (strftime('%w', arrival_from) as integer)
  when 0 then 'Sunday'
  when 1 then 'Monday'
  when 2 then 'Tuesday'
  when 3 then 'Wednesday'
  when 4 then 'Thursday'
  when 5 then 'Friday'
  else 'Saturday' end as arrival_from_day,arrival_from, link_to, link_from 
  from flights where 1=1
  and fly_to like '%SKG%'
  and arrival_from_day in ('Saturday', 'Sunday', 'Monday')
  and departure_to_day in ('Tuesday', 'Wednesday', 'Thursday', 'Friday')
  and hours > 72
  and hours < 110
  and departure_to > '2023-07-01'
  order by discount_price asc
  