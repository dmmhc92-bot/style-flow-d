import React, { useState } from 'react';
import {
  View,
  Text,
  StyleSheet,
  TextInput,
  TouchableOpacity,
  ScrollView,
} from 'react-native';
import { Ionicons } from '@expo/vector-icons';
import Colors from '../constants/Colors';
import Spacing from '../constants/Spacing';
import Typography from '../constants/Typography';

// Common stylist specialties for suggestions
const SUGGESTED_SPECIALTIES = [
  'Colorist',
  'Balayage',
  'Highlights',
  'Extensions',
  'Cuts',
  'Braiding',
  'Natural Hair',
  'Curly Hair',
  'Blowouts',
  'Updos',
  'Bridal',
  'Men\'s Cuts',
  'Kids',
  'Keratin',
  'Perms',
  'Vivid Colors',
];

interface SpecialtiesInputProps {
  value: string[];
  onChange: (specialties: string[]) => void;
  maxSpecialties?: number;
  label?: string;
}

/**
 * SpecialtiesInput - Multi-select chip input for stylist specialties
 * 
 * Features:
 * - Add custom specialties by typing
 * - Quick-add from suggested specialties
 * - Remove by tapping chip X
 * - Maximum limit option
 */
export const SpecialtiesInput: React.FC<SpecialtiesInputProps> = ({
  value = [],
  onChange,
  maxSpecialties = 8,
  label = 'Specialties',
}) => {
  const [inputText, setInputText] = useState('');
  const [showSuggestions, setShowSuggestions] = useState(false);
  
  const addSpecialty = (specialty: string) => {
    const trimmed = specialty.trim();
    if (!trimmed) return;
    
    // Check if already exists (case-insensitive)
    if (value.some(s => s.toLowerCase() === trimmed.toLowerCase())) {
      return;
    }
    
    // Check max limit
    if (value.length >= maxSpecialties) {
      return;
    }
    
    onChange([...value, trimmed]);
    setInputText('');
  };
  
  const removeSpecialty = (index: number) => {
    const newSpecialties = [...value];
    newSpecialties.splice(index, 1);
    onChange(newSpecialties);
  };
  
  const handleInputSubmit = () => {
    if (inputText.trim()) {
      addSpecialty(inputText);
    }
  };
  
  // Filter suggestions that aren't already selected
  const availableSuggestions = SUGGESTED_SPECIALTIES.filter(
    s => !value.some(v => v.toLowerCase() === s.toLowerCase())
  );
  
  // Filter based on input text
  const filteredSuggestions = inputText
    ? availableSuggestions.filter(s => 
        s.toLowerCase().includes(inputText.toLowerCase())
      )
    : availableSuggestions;
  
  return (
    <View style={styles.container}>
      <Text style={styles.label}>{label}</Text>
      
      {/* Selected Specialties */}
      {value.length > 0 && (
        <View style={styles.chipsContainer}>
          {value.map((specialty, index) => (
            <View key={index} style={styles.chip}>
              <Ionicons name="sparkles" size={12} color={Colors.accent} />
              <Text style={styles.chipText}>{specialty}</Text>
              <TouchableOpacity
                onPress={() => removeSpecialty(index)}
                hitSlop={{ top: 10, bottom: 10, left: 10, right: 10 }}
              >
                <Ionicons name="close-circle" size={16} color={Colors.textSecondary} />
              </TouchableOpacity>
            </View>
          ))}
        </View>
      )}
      
      {/* Input Field */}
      {value.length < maxSpecialties && (
        <View style={styles.inputContainer}>
          <Ionicons name="add-circle-outline" size={20} color={Colors.textSecondary} />
          <TextInput
            style={styles.input}
            value={inputText}
            onChangeText={setInputText}
            placeholder="Add a specialty..."
            placeholderTextColor={Colors.textLight}
            onSubmitEditing={handleInputSubmit}
            onFocus={() => setShowSuggestions(true)}
            returnKeyType="done"
            autoCapitalize="words"
          />
          {inputText.length > 0 && (
            <TouchableOpacity onPress={handleInputSubmit} style={styles.addButton}>
              <Text style={styles.addButtonText}>Add</Text>
            </TouchableOpacity>
          )}
        </View>
      )}
      
      {/* Counter */}
      <Text style={styles.counter}>
        {value.length}/{maxSpecialties} specialties
      </Text>
      
      {/* Suggestions */}
      {showSuggestions && filteredSuggestions.length > 0 && value.length < maxSpecialties && (
        <View style={styles.suggestionsContainer}>
          <Text style={styles.suggestionsLabel}>Quick add:</Text>
          <ScrollView 
            horizontal 
            showsHorizontalScrollIndicator={false}
            contentContainerStyle={styles.suggestionsScroll}
          >
            {filteredSuggestions.slice(0, 10).map((suggestion, index) => (
              <TouchableOpacity
                key={index}
                style={styles.suggestionChip}
                onPress={() => addSpecialty(suggestion)}
              >
                <Ionicons name="add" size={14} color={Colors.accent} />
                <Text style={styles.suggestionText}>{suggestion}</Text>
              </TouchableOpacity>
            ))}
          </ScrollView>
        </View>
      )}
    </View>
  );
};

const styles = StyleSheet.create({
  container: {
    marginBottom: Spacing.md,
  },
  label: {
    fontSize: Typography.bodySmall,
    fontWeight: Typography.medium as any,
    color: Colors.text,
    marginBottom: Spacing.sm,
  },
  chipsContainer: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    gap: Spacing.xs,
    marginBottom: Spacing.sm,
  },
  chip: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: Colors.accent + '15',
    paddingLeft: Spacing.sm,
    paddingRight: 6,
    paddingVertical: 6,
    borderRadius: 16,
    gap: 4,
  },
  chipText: {
    fontSize: Typography.bodySmall,
    color: Colors.accent,
    fontWeight: Typography.medium as any,
  },
  inputContainer: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: Colors.backgroundSecondary,
    borderRadius: 12,
    paddingHorizontal: Spacing.md,
    borderWidth: 1,
    borderColor: Colors.border,
    gap: Spacing.sm,
  },
  input: {
    flex: 1,
    fontSize: Typography.body,
    color: Colors.text,
    paddingVertical: Spacing.md,
  },
  addButton: {
    backgroundColor: Colors.accent,
    paddingHorizontal: Spacing.md,
    paddingVertical: 6,
    borderRadius: 8,
  },
  addButtonText: {
    fontSize: Typography.bodySmall,
    color: Colors.background,
    fontWeight: Typography.semibold as any,
  },
  counter: {
    fontSize: Typography.caption,
    color: Colors.textLight,
    marginTop: Spacing.xs,
    textAlign: 'right',
  },
  suggestionsContainer: {
    marginTop: Spacing.sm,
  },
  suggestionsLabel: {
    fontSize: Typography.caption,
    color: Colors.textSecondary,
    marginBottom: Spacing.xs,
  },
  suggestionsScroll: {
    gap: Spacing.xs,
  },
  suggestionChip: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: Colors.backgroundSecondary,
    paddingHorizontal: Spacing.sm,
    paddingVertical: 6,
    borderRadius: 12,
    borderWidth: 1,
    borderColor: Colors.border,
    gap: 2,
    marginRight: Spacing.xs,
  },
  suggestionText: {
    fontSize: Typography.caption,
    color: Colors.text,
  },
});

export default SpecialtiesInput;
