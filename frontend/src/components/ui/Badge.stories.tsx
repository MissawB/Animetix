import type { Meta, StoryObj } from '@storybook/react';
import { Badge } from './Badge';

const meta = {
  title: 'UI/Badge',
  component: Badge,
  parameters: {
    layout: 'centered',
  },
  tags: ['autodocs'],
  argTypes: {
    variant: {
      control: { type: 'select' },
      options: ['primary', 'success', 'danger', 'warning', 'neutral'],
    },
  },
} satisfies Meta<typeof Badge>;

export default meta;
type Story = StoryObj<typeof meta>;

export const Neutral: Story = {
  args: {
    variant: 'neutral',
    children: 'Niveau 1',
  },
};

export const Primary: Story = {
  args: {
    variant: 'primary',
    children: 'Nouveau',
  },
};

export const Success: Story = {
  args: {
    variant: 'success',
    children: 'Validé',
  },
};

export const Danger: Story = {
  args: {
    variant: 'danger',
    children: 'Erreur',
  },
};

export const Warning: Story = {
  args: {
    variant: 'warning',
    children: 'En cours',
  },
};
