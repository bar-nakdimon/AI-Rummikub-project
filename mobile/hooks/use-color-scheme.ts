import { useColorScheme as useRNColorScheme } from 'react-native';

/**
 * React Native can also report 'unspecified'; the app only has light and dark themes
 */
export function useColorScheme(): 'light' | 'dark' {
  return useRNColorScheme() === 'dark' ? 'dark' : 'light';
}
