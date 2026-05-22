import type { Meta, StoryObj } from '@storybook/react';
import { Button } from './Button';

const meta = {
  title: 'UI/Button',
  component: Button,
  parameters: {
    layout: 'centered',
  },
  tags: ['autodocs'],
  argTypes: {
    variant: {
      control: { type: 'select' },
      options: ['primary', 'secondary', 'danger', 'success', 'outline'],
    },
    size: {
      control: { type: 'select' },
      options: ['sm', 'md', 'lg'],
    },
    fullWidth: {
      control: 'boolean',
    },
    disabled: {
      control: 'boolean',
    },
  },
} satisfies Meta<typeof Button>;

export default meta;
type Story = StoryObj<typeof meta>;

export const Primary: Story = {
  args: {
    variant: 'primary',
    children: 'Action Principale',
  },
};

export const Secondary: Story = {
  args: {
    variant: 'secondary',
    children: 'Action Secondaire',
  },
};

export const Danger: Story = {
  args: {
    variant: 'danger',
    children: 'Supprimer',
  },
};

export const Success: Story = {
  args: {
    variant: 'success',
    children: 'Valider',
  },
};

export const Outline: Story = {
  args: {
    variant: 'outline',
    children: 'Annuler',
  },
};

export const Small: Story = {
  args: {
    size: 'sm',
    children: 'Petit Bouton',
  },
};

export const Large: Story = {
  args: {
    size: 'lg',
    children: 'Grand Bouton',
  },
};

export const Disabled: Story = {
  args: {
    disabled: true,
    children: 'Non disponible',
  },
};

export const FullWidth: Story = {
  args: {
    fullWidth: true,
    children: 'Bouton Pleine Largeur',
  },
  parameters: {
    layout: 'padded',
  },
};
