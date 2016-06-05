This module creates a binary sensor that indicates whether it is daylight (on) or nighttime(off), which is useful in combination with logical rules.

This module calculates the sunset and sunrise times based on the longtitude and latitude that you configure and compares that with the current system time to determine whether the sun is in the sky or not (so no internet connection needed). It also allows to configure what counts as sun up or down: official twilight, civil twilight, nautical twilight or astronomical twilight (see wikipedia for definitions).

Using this sensor you can make a logical rule to trigger actions when the sun sets or rises, i.e. when the value of this sensor changes.

Also, you can make scenes that behave differently during daytime or night time. Just make three scenes: one empty one, one for daytime and one for night time. Then make two logical rules: one that triggers the daytime scene when the empty scene is triggered and the Daylight sensor is on, and one that triggers the night time scene when the empty scene is triggered when the Daylight sensor is off.
Hide these daytime and nighttime scenes and only put the empty scene on the dashboard. Now when you trigger the "empty" scene you will get different behavior based on whether it is day or night time.

Module image based on icon made by Freepik (http://www.flaticon.com/authors/freepik) licensed by Creative Commons BY 3.0 (http://creativecommons.org/licenses/by/3.0/)
