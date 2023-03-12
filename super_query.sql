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
  from flights where ((departure_to_day = 'Thursday' and strftime("%H:%M", departure_to) > '19:00') or departure_to_day = 'Friday') AND
  ((arrival_from_day = 'Sunday' and strftime("%H:%M", arrival_from) < '12:00') or arrival_from_day = 'Saturday') AND discount_price < 500 
  and fly_to like '%Rome%'
  order by discount_price asc
  