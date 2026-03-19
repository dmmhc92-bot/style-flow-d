import AsyncStorage from '@react-native-async-storage/async-storage';

export const storage = {
  async setToken(token: string) {
    await AsyncStorage.setItem('authToken', token);
  },
  
  async getToken() {
    return await AsyncStorage.getItem('authToken');
  },
  
  async removeToken() {
    await AsyncStorage.removeItem('authToken');
  },
  
  async setUserData(userData: any) {
    await AsyncStorage.setItem('userData', JSON.stringify(userData));
  },
  
  async getUserData() {
    const data = await AsyncStorage.getItem('userData');
    return data ? JSON.parse(data) : null;
  },
  
  async removeUserData() {
    await AsyncStorage.removeItem('userData');
  },
  
  async clearAll() {
    await AsyncStorage.clear();
  },
};