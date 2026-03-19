import React from 'react';
import { View, Text, StyleSheet } from 'react-native';
import { Ionicons } from '@expo/vector-icons';
import Button from './Button';
import Colors from '../constants/Colors';
import Spacing from '../constants/Spacing';
import Typography from '../constants/Typography';

interface EmptyStateProps {
  icon: string;
  title: string;
  description: string;
  actionLabel: string;
  onAction: () => void;
}

export default function EmptyState({
  icon,
  title,
  description,
  actionLabel,
  onAction,
}: EmptyStateProps) {
  return (
    <View style={styles.container}>
      <View style={styles.iconContainer}>
        <Ionicons name={icon as any} size={56} color={Colors.accent} />
      </View>
      <Text style={styles.title}>{title}</Text>
      <Text style={styles.description}>{description}</Text>
      <Button
        title={actionLabel}
        onPress={onAction}
        style={styles.button}
      />
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
    paddingHorizontal: Spacing.xl,
    paddingVertical: Spacing.xxxl,
  },
  iconContainer: {
    width: 100,
    height: 100,
    borderRadius: Spacing.radiusFull,
    backgroundColor: Colors.accent + '20',
    alignItems: 'center',
    justifyContent: 'center',
    marginBottom: Spacing.lg,
    borderWidth: 2,
    borderColor: Colors.accent + '40',
  },
  title: {
    fontSize: Typography.h3,
    fontWeight: Typography.bold,
    color: Colors.text,
    marginBottom: Spacing.sm,
    textAlign: 'center',
  },
  description: {
    fontSize: Typography.body,
    color: Colors.textSecondary,
    textAlign: 'center',
    marginBottom: Spacing.xl,
    lineHeight: Typography.body * Typography.lineHeightNormal,
    maxWidth: 300,
  },
  button: {
    paddingHorizontal: Spacing.xl + Spacing.md,
  },
});