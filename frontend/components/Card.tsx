import React from 'react';
import { View, StyleSheet } from 'react-native';
import Colors from '../constants/Colors';
import Spacing from '../constants/Spacing';
import Typography from '../constants/Typography';

interface CardProps {
  children: React.ReactNode;
  style?: any;
  onPress?: () => void;
}

export function Card({ children, style, onPress }: CardProps) {
  const Container: any = onPress ? require('react-native').TouchableOpacity : View;
  
  return (
    <Container
      style={[styles.card, style]}
      onPress={onPress}
      activeOpacity={onPress ? 0.85 : 1}
    >
      {children}
    </Container>
  );
}

const styles = StyleSheet.create({
  card: {
    backgroundColor: Colors.backgroundCard,
    borderRadius: Spacing.radiusLarge,
    padding: Spacing.cardPadding,
    borderWidth: 1,
    borderColor: Colors.border,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 8 },
    shadowOpacity: 0.3,
    shadowRadius: 16,
    elevation: 8,
  },
});