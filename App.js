import React from "react";
import { NavigationContainer } from "@react-navigation/native";
import { createNativeStackNavigator } from "@react-navigation/native-stack";

import Login from "./pages/Login";
import Register from "./pages/Register";
import BottomNavBar from "./pages/BottomNavBar";


const Stack = createNativeStackNavigator();

const App = () => {
  return (
      <NavigationContainer>
        <Stack.Navigator initialRouteName="Login">
          <Stack.Screen
              name="Login"
              component={Login}
              options={{ headerShown: false }}
          />
          <Stack.Screen
              name="Register"
              component={Register}
              options={{ headerShown: false }}
          />
          <Stack.Screen
              name="EyeZen"
              component={BottomNavBar}
              options={{ headerShown: false }}
          />
        
      </Stack.Navigator>
    </NavigationContainer>
  );
};

export default App;
